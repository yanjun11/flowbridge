"""Webhook 接收端点"""

import json
import logging

from fastapi import APIRouter, HTTPException, Request

from src.dao.orm.model import Workflow
from src.service.cache import check_and_set_processed
from src.service.executor import WorkflowExecutor
from src.service.plugin_manager import PluginManager

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)


@router.post("/feishu/bitable")
async def feishu_bitable_webhook(request: Request):
    """接收飞书多维表格 webhook"""
    body = await request.body()
    headers = dict(request.headers)

    # 获取触发器插件
    plugin_manager = PluginManager()
    trigger = plugin_manager.get_trigger("feishu_bitable")
    if trigger is None:
        raise HTTPException(status_code=503, detail="Trigger plugin not available")

    # 验证签名
    if not await trigger.verify_signature(body, headers):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # 解析事件
    raw_data = json.loads(body)
    trigger_data = await trigger.parse_event(raw_data)

    if not trigger_data:
        return {"message": "Event ignored"}

    # 事件去重
    event_id = trigger_data.get("event_id")
    if not event_id:
        logger.warning("Missing event_id in feishu_bitable trigger_data")
    if event_id:
        try:
            is_new_event = await check_and_set_processed(event_id)
        except Exception as e:
            logger.error("Failed to deduplicate webhook event: %s", e)
            raise HTTPException(status_code=503, detail="Event deduplication unavailable")
        if not is_new_event:
            return {"message": "Duplicate event ignored"}

    # 查找匹配的工作流
    workflows = await Workflow.filter(trigger_type="feishu_bitable", status="active").all()

    # 执行所有匹配的工作流
    executor = WorkflowExecutor()
    for workflow in workflows:
        logger.info(
            "Dispatching matched feishu_bitable workflow",
            extra={"workflow_id": str(workflow.id)},
        )
        await executor.execute(workflow.id, trigger_data)

    return {"message": "OK", "workflows_triggered": len(workflows)}


@router.post("/feishu/approval")
async def feishu_approval_webhook(request: Request):
    """接收飞书审批 webhook"""
    body = await request.body()
    headers = dict(request.headers)

    # 获取触发器插件
    plugin_manager = PluginManager()
    trigger = plugin_manager.get_trigger("feishu_approval")
    if trigger is None:
        raise HTTPException(status_code=503, detail="Trigger plugin not available")

    # 验证签名
    if not await trigger.verify_signature(body, headers):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # 解析事件
    raw_data = json.loads(body)
    trigger_data = await trigger.parse_event(raw_data)

    if not trigger_data:
        return {"message": "Event ignored"}

    # 事件去重
    event_id = trigger_data.get("event_id")
    if not event_id:
        logger.warning("Missing event_id in feishu_approval trigger_data")
    if event_id:
        try:
            is_new_event = await check_and_set_processed(event_id)
        except Exception as e:
            logger.error("Failed to deduplicate webhook event: %s", e)
            raise HTTPException(status_code=503, detail="Event deduplication unavailable")
        if not is_new_event:
            return {"message": "Duplicate event ignored"}

    # 查找匹配的工作流
    workflows = await Workflow.filter(trigger_type="feishu_approval", status="active").all()

    approval_code = trigger_data.get("approval_code")
    matched_workflows = [
        workflow
        for workflow in workflows
        if isinstance(workflow.trigger_config, dict) and workflow.trigger_config.get("approval_code") == approval_code
    ]

    # 执行所有匹配的工作流
    executor = WorkflowExecutor()
    for workflow in matched_workflows:
        logger.info(
            "Dispatching matched feishu_approval workflow",
            extra={"workflow_id": str(workflow.id)},
        )
        await executor.execute(workflow.id, trigger_data)

    return {"message": "OK", "workflows_triggered": len(matched_workflows)}
