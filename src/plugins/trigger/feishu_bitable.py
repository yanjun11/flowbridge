"""飞书多维表格触发器"""

import base64
import hashlib
import hmac
import logging
import time
from typing import Any, Dict, Optional

from src.plugins.base import TriggerPlugin

logger = logging.getLogger(__name__)


class FeishuBitableTrigger(TriggerPlugin):
    """飞书多维表格触发器"""

    @property
    def trigger_type(self) -> str:
        return "feishu_bitable"

    async def validate_config(self, config: Dict[str, Any]) -> bool:
        required = ["app_id", "app_secret"]
        return all(key in config for key in required)

    async def parse_event(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            header = raw_data.get("header", {})
            if header.get("event_type") != "bitable.record.created":
                return None

            event = raw_data.get("event", {})
            record = event.get("record", {})
            return {
                "event_id": header.get("event_id"),
                "app_token": event.get("app_token"),
                "table_id": event.get("table_id"),
                "record_id": record.get("record_id"),
                "fields": record.get("fields", {}),
            }
        except Exception as e:
            logger.error(f"Failed to parse feishu bitable event: {e}")
            return None

    async def verify_signature(self, request_data: bytes, headers: Dict[str, str]) -> bool:
        try:
            timestamp = self._get_header(headers, "X-Lark-Request-Timestamp")
            nonce = self._get_header(headers, "X-Lark-Request-Nonce")
            signature = self._get_header(headers, "X-Lark-Signature")

            if not all([timestamp, signature]):
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
