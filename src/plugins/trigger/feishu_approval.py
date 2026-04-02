"""飞书审批触发器"""
import base64
import hashlib
import hmac
import json
import logging
import time
from typing import Any, Dict, Optional

from src.plugins.base import TriggerPlugin

logger = logging.getLogger(__name__)
RESERVED_KEYS = {"event_id", "approval_code", "instance_code", "status", "operator_open_id"}


class FeishuApprovalTrigger(TriggerPlugin):
    """飞书审批触发器"""

    @property
    def trigger_type(self) -> str:
        return "feishu_approval"

    async def validate_config(self, config: Dict[str, Any]) -> bool:
        required = ["approval_code"]
        return all(key in config for key in required)

    async def parse_event(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            header = raw_data.get("header", {})
            if header.get("event_type") != "approval_instance":
                return None

            event = raw_data.get("event", {})
            status = event.get("status")
            if status != "APPROVED":
                return None

            trigger_data = {
                "event_id": header.get("event_id"),
                "approval_code": event.get("approval_code"),
                "instance_code": event.get("instance_code"),
                "status": status,
                "operator_open_id": event.get("operator_open_id"),
            }

            form_raw = event.get("form")
            if isinstance(form_raw, str) and form_raw:
                try:
                    form_items = json.loads(form_raw)
                    if isinstance(form_items, list):
                        for item in form_items:
                            if not isinstance(item, dict):
                                continue
                            name = item.get("name")
                            value = item.get("value")
                            if name and name not in RESERVED_KEYS:
                                trigger_data[name] = value
                except Exception as e:
                    logger.warning(f"Failed to parse feishu approval form data: {e}")

            return trigger_data
        except Exception as e:
            logger.error(f"Failed to parse feishu approval event: {e}")
            return None

    async def verify_signature(self, request_data: bytes, headers: Dict[str, str]) -> bool:
        try:
            timestamp = self._get_header(headers, "X-Lark-Request-Timestamp")
            nonce = self._get_header(headers, "X-Lark-Request-Nonce")
            signature = self._get_header(headers, "X-Lark-Signature")

            if not all([timestamp, nonce, signature]):
                return False

            try:
                ts = int(timestamp)
            except (TypeError, ValueError):
                return False

            now = int(time.time())
            if abs(now - ts) > 300:
                return False

            from src.conf import settings
            secret = settings.feishu_webhook_secret
            if not secret:
                return False

            string_to_sign = f"{timestamp}\n{nonce}\n{request_data.decode('utf-8')}"
            hmac_code = hmac.new(secret.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha256).digest()
            calculated_signature = base64.b64encode(hmac_code).decode("utf-8")
            return hmac.compare_digest(signature, calculated_signature)
        except Exception as e:
            logger.error(f"Failed to verify feishu signature: {e}")
            return False

    @staticmethod
    def _get_header(headers: Dict[str, str], name: str) -> str:
        return headers.get(name, "") or headers.get(name.lower(), "")
