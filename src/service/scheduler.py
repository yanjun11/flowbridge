"""Cron 定时任务调度器。"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.dao.orm.model import Workflow

logger = logging.getLogger(__name__)


class CronScheduler:
    """管理 cron 类型工作流的定时调度。"""

    _instance: "CronScheduler | None" = None

    def __new__(cls) -> "CronScheduler":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._scheduler = AsyncIOScheduler()
        return cls._instance

    _scheduler: AsyncIOScheduler

    async def start(self) -> None:
        try:
            if self._scheduler.running:
                logger.info("CronScheduler already running")
                return
            workflows = await Workflow.filter(trigger_type="cron", status="active").all()
            for workflow in workflows:
                self._add_job(workflow)
            self._scheduler.start()
            logger.info("CronScheduler started with %d jobs", len(workflows))
        except Exception:
            logger.exception("Failed to start CronScheduler")

    def shutdown(self) -> None:
        try:
            if self._scheduler.running:
                self._scheduler.shutdown(wait=False)
                logger.info("CronScheduler shutdown")
        except Exception:
            logger.exception("Failed to shutdown CronScheduler")

    def add_workflow(self, workflow: Workflow) -> None:
        try:
            if workflow.trigger_type != "cron" or workflow.status != "active":
                return
            self._add_job(workflow)
        except Exception:
            logger.exception("Failed to add cron workflow: workflow_id=%s", workflow.id)

    def remove_workflow(self, workflow_id: UUID) -> None:
        try:
            job_id = self._job_id(workflow_id)
            if self._scheduler.get_job(job_id):
                self._scheduler.remove_job(job_id)
                logger.info("Removed cron job: %s", job_id)
        except Exception:
            logger.exception("Failed to remove cron workflow: workflow_id=%s", workflow_id)

    def update_workflow(self, workflow: Workflow) -> None:
        try:
            self.remove_workflow(workflow.id)
            self.add_workflow(workflow)
        except Exception:
            logger.exception("Failed to update cron workflow: workflow_id=%s", workflow.id)

    def _add_job(self, workflow: Workflow) -> None:
        try:
            config = workflow.trigger_config or {}
            cron_expr = config.get("cron_expression", "")
            tz = config.get("timezone", "Asia/Shanghai")
            parts = cron_expr.strip().split()
            if len(parts) != 5:
                logger.warning("Invalid cron expression for workflow %s: %s", workflow.id, cron_expr)
                return

            trigger = CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4],
                timezone=tz,
            )
            job_id = self._job_id(workflow.id)
            if self._scheduler.get_job(job_id):
                self._scheduler.remove_job(job_id)

            self._scheduler.add_job(
                self._execute_workflow,
                trigger,
                id=job_id,
                args=[workflow.id, cron_expr],
                replace_existing=True,
            )
            logger.info("Added cron job: %s cron=%s tz=%s", job_id, cron_expr, tz)
        except Exception:
            logger.exception("Failed to add cron job: workflow_id=%s", workflow.id)

    @staticmethod
    async def _execute_workflow(workflow_id: UUID, cron_expression: str) -> None:
        from src.service.executor import WorkflowExecutor

        trigger_data = {
            "scheduled_time": datetime.now(timezone.utc).isoformat(),
            "cron_expression": cron_expression,
            "trigger_type": "cron",
        }
        executor = WorkflowExecutor()
        try:
            execution_id = await executor.execute(workflow_id, trigger_data)
            logger.info(
                "Cron workflow executed: workflow_id=%s execution_id=%s",
                workflow_id,
                execution_id,
                extra={"workflow_id": str(workflow_id), "execution_id": str(execution_id)},
            )
        except Exception:
            logger.exception(
                "Cron workflow execution failed: workflow_id=%s",
                workflow_id,
                extra={"workflow_id": str(workflow_id)},
            )

    @staticmethod
    def _job_id(workflow_id: UUID) -> str:
        return f"cron_{workflow_id}"
