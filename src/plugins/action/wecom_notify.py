"""企微群通知动作"""
import ipaddress
import logging
import socket
from typing import Any, Dict
from urllib.parse import urlparse

import httpx

from src.plugins.base import ActionPlugin, ActionResult
from src.service.template import render_template

logger = logging.getLogger(__name__)


class WecomNotifyAction(ActionPlugin):
    """企微群通知动作"""

    @property
    def action_type(self) -> str:
        return "wecom_notify"

    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置"""
        return "webhook_url" in config and "message" in config

    async def execute(self, context: Dict[str, Any], config: Dict[str, Any]) -> ActionResult:
        """执行动作"""
        try:
            webhook_url = config["webhook_url"]
            if not self._is_safe_webhook_url(webhook_url):
                return ActionResult(success=False, message="Webhook URL 不安全，仅允许公网 HTTPS 地址")
            message_template = config["message"]
            message = render_template(message_template, context)

            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(webhook_url, json={"msgtype": "text", "text": {"content": message}})

            if resp.status_code == 200:
                data = resp.json()
                if data.get("errcode") == 0:
                    return ActionResult(success=True, message="通知发送成功", data={"response": data})
                else:
                    return ActionResult(success=False, message=f"企微返回错误: {data.get('errmsg')}")
            else:
                return ActionResult(success=False, message=f"HTTP 错误: {resp.status_code}")
        except Exception as e:
            logger.error(f"Failed to send wecom notification: {e}")
            return ActionResult(success=False, message=f"发送失败: {str(e)}")

    @staticmethod
    def _is_safe_webhook_url(url: str) -> bool:
        try:
            parsed = urlparse(url)
            if parsed.scheme != "https":
                return False

            hostname = parsed.hostname
            if not hostname:
                return False

            host_lower = hostname.lower()
            if host_lower in {"localhost", "127.0.0.1", "::1"}:
                return False

            try:
                ip = ipaddress.ip_address(hostname)
                return not (
                    ip.is_private
                    or ip.is_loopback
                    or ip.is_link_local
                    or ip.is_reserved
                    or ip.is_multicast
                    or ip.is_unspecified
                )
            except ValueError:
                pass

            for result in socket.getaddrinfo(hostname, parsed.port or 443, type=socket.SOCK_STREAM):
                resolved_ip = ipaddress.ip_address(result[4][0])
                if (
                    resolved_ip.is_private
                    or resolved_ip.is_loopback
                    or resolved_ip.is_link_local
                    or resolved_ip.is_reserved
                    or resolved_ip.is_multicast
                    or resolved_ip.is_unspecified
                ):
                    return False

            return True
        except Exception:
            return False
