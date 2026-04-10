"""告警通知服务。"""

import logging

import httpx

from src.conf import settings

logger = logging.getLogger(__name__)


async def send_failure_alert(
    workflow_name: str,
    workflow_id: str,
    execution_id: str,
    status: str,
    error_message: str,
    execution_time_ms: int,
) -> None:
    """发送工作流失败/超时告警，任何异常都仅记录日志。"""
    try:
        if not settings.alert_webhook_url:
            return

        status_label = {"failed": "失败", "timeout": "超时"}.get(status, status)
        alert_text = (
            f"[FlowBridge 告警] 工作流执行{status_label}\n"
            f"工作流: {workflow_name} ({workflow_id})\n"
            f"执行ID: {execution_id}\n"
            f"状态: {status_label}\n"
            f"错误: {error_message}\n"
            f"耗时: {execution_time_ms}ms"
        )

        payload = {"msg_type": "text", "content": {"text": alert_text}}
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(settings.alert_webhook_url, json=payload)
    except Exception:
        logger.exception(
            "Failed to send workflow alert: workflow_id=%s execution_id=%s status=%s",
            workflow_id,
            execution_id,
            status,
        )
