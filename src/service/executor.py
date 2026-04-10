"""工作流执行引擎。"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID

from src.dao.orm.model import ActionExecution, Workflow, WorkflowExecution
from src.service.alerting import send_failure_alert
from src.service.plugin_manager import PluginManager
from src.service.template import render_template

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """工作流执行器。"""

    MAX_RETRIES = 3
    TIMEOUT_SECONDS = 30

    def __init__(self, plugin_manager: PluginManager | None = None) -> None:
        self.plugin_manager = plugin_manager or PluginManager()

    async def execute(self, workflow_id: UUID, trigger_data: Dict[str, Any]) -> UUID:
        """执行工作流，返回执行记录 ID。"""
        workflow = await Workflow.get_or_none(id=workflow_id)
        if workflow is None:
            raise ValueError(f"Workflow not found: {workflow_id}")
        if workflow.status != "active":
            raise ValueError(f"Workflow is not active: {workflow_id}, status={workflow.status}")

        execution = await WorkflowExecution.create(
            workflow_id=workflow_id,
            trigger_data=trigger_data,
            status="running",
        )
        start = time.perf_counter()

        try:
            await asyncio.wait_for(
                self._run_actions(workflow=workflow, execution_id=execution.id, trigger_data=trigger_data),
                timeout=self.TIMEOUT_SECONDS,
            )
            status = "success"
            error_message = None
        except asyncio.TimeoutError:
            logger.exception(
                "Workflow execution timeout: workflow_id=%s execution_id=%s",
                workflow_id,
                execution.id,
                extra={"workflow_id": str(workflow_id), "execution_id": str(execution.id)},
            )
            status = "timeout"
            error_message = "Workflow execution timeout"
        except Exception as exc:
            logger.exception(
                "Workflow execution failed: workflow_id=%s execution_id=%s",
                workflow_id,
                execution.id,
                extra={"workflow_id": str(workflow_id), "execution_id": str(execution.id)},
            )
            status = "failed"
            error_message = str(exc)

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        execution.status = status
        execution.error_message = error_message
        execution.execution_time_ms = elapsed_ms
        execution.completed_at = datetime.now(timezone.utc)
        await execution.save()

        if status in ("failed", "timeout"):
            await send_failure_alert(
                workflow_name=workflow.name,
                workflow_id=str(workflow_id),
                execution_id=str(execution.id),
                status=status,
                error_message=error_message or "",
                execution_time_ms=elapsed_ms,
            )

        return execution.id

    async def _run_actions(self, workflow: Workflow, execution_id: UUID, trigger_data: Dict[str, Any]) -> None:
        actions = workflow.actions or []
        context: Dict[str, Any] = {"trigger": trigger_data, "actions": []}

        for index, action in enumerate(actions):
            if not isinstance(action, dict):
                raise ValueError(f"Invalid action config at index {index}, expected dict")
            action_type = str(action.get("type") or action.get("action_type") or "")
            action_config = action.get("config") or action.get("action_config") or {}
            if not action_type:
                raise ValueError(f"Invalid action type at index {index}")

            action_execution = await ActionExecution.create(
                execution_id=execution_id,
                action_type=action_type,
                action_config=action_config,
                action_index=index,
                status="running",
            )

            plugin = self.plugin_manager.get_action(action_type)
            if plugin is None:
                action_execution.status = "failed"
                action_execution.error_message = f"Action plugin not found: {action_type}"
                action_execution.completed_at = datetime.now(timezone.utc)
                await action_execution.save()
                raise ValueError(action_execution.error_message)

            rendered_config = self._render_action_config(action_config, context)
            last_error: str | None = None
            success = False

            for attempt in range(self.MAX_RETRIES):
                try:
                    result = await plugin.execute(context=context, config=rendered_config)
                    if not result.success:
                        raise RuntimeError(result.message or "Action execution failed")

                    action_execution.status = "success"
                    action_execution.retry_count = attempt
                    action_execution.result = {"message": result.message, "data": result.data}
                    action_execution.completed_at = datetime.now(timezone.utc)
                    await action_execution.save()

                    context["actions"].append({"type": action_type, "result": action_execution.result})
                    success = True
                    break
                except Exception as exc:
                    last_error = str(exc)
                    logger.warning(
                        "Action execution failed, retrying: execution_id=%s action_type=%s attempt=%s/%s error=%s",
                        execution_id,
                        action_type,
                        attempt + 1,
                        self.MAX_RETRIES,
                        last_error,
                        extra={"workflow_id": str(workflow.id), "execution_id": str(execution_id)},
                    )

                    if attempt < self.MAX_RETRIES - 1:
                        await asyncio.sleep(2**attempt)

            if not success:
                action_execution.status = "failed"
                action_execution.error_message = last_error
                action_execution.retry_count = self.MAX_RETRIES - 1
                action_execution.completed_at = datetime.now(timezone.utc)
                await action_execution.save()
                raise RuntimeError(f"Action failed after retries: {action_type}, error={last_error}")

    def _render_action_config(self, action_config: Any, context: Dict[str, Any]) -> Any:
        """递归渲染动作配置中的模板字符串。"""
        if isinstance(action_config, str):
            return render_template(action_config, context)
        if isinstance(action_config, list):
            return [self._render_action_config(item, context) for item in action_config]
        if isinstance(action_config, dict):
            return {key: self._render_action_config(value, context) for key, value in action_config.items()}
        return action_config
