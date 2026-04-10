"""飞书机器人通知动作"""

import json
import logging
from typing import Any, Dict

import httpx

from src.plugins.action.wecom_notify import WecomNotifyAction
from src.plugins.base import ActionPlugin, ActionResult
from src.service.template import render_template

logger = logging.getLogger(__name__)


class FeishuNotifyAction(ActionPlugin):
    """飞书机器人通知动作"""

    @property
    def action_type(self) -> str:
        return "feishu_notify"

    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置"""
        return "webhook_url" in config and "message" in config

    async def execute(self, context: Dict[str, Any], config: Dict[str, Any]) -> ActionResult:
        """执行动作"""
        try:
            webhook_url = config["webhook_url"]
            if not WecomNotifyAction._is_safe_webhook_url(webhook_url):
                return ActionResult(success=False, message="Webhook URL 不安全，仅允许公网 HTTPS 地址")

            msg_type = str(config.get("msg_type", "text")).strip().lower()
            message = render_template(config["message"], context)
            payload = self._build_payload(msg_type, message)
            if payload is None:
                return ActionResult(success=False, message=f"不支持的消息类型: {msg_type}")

            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(webhook_url, json=payload)

            if resp.status_code != 200:
                return ActionResult(success=False, message=f"HTTP 错误: {resp.status_code}")

            data = resp.json()
            if data.get("code") == 0:
                return ActionResult(success=True, message="通知发送成功", data={"response": data})
            return ActionResult(success=False, message=f"飞书返回错误: {data.get('msg') or data}")
        except json.JSONDecodeError as e:
            return ActionResult(success=False, message=f"interactive card JSON 解析失败: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to send feishu notification: {e}")
            return ActionResult(success=False, message=f"发送失败: {str(e)}")

    @staticmethod
    def _build_payload(msg_type: str, message: str) -> Dict[str, Any] | None:
        if msg_type == "text":
            return {"msg_type": "text", "content": {"text": message}}

        if msg_type in {"rich_text", "post"}:
            return {
                "msg_type": "post",
                "content": {
                    "post": {
                        "zh_cn": {
                            "content": [[{"tag": "text", "text": message}]],
                        }
                    }
                },
            }

        if msg_type == "interactive":
            card = json.loads(message)
            if not isinstance(card, dict):
                raise json.JSONDecodeError("card must be a JSON object", message, 0)
            return {"msg_type": "interactive", "card": card}

        return None
