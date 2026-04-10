"""Cron 定时触发器。"""

import logging
from typing import Any, Dict, Optional

from src.plugins.base import TriggerPlugin

logger = logging.getLogger(__name__)


class CronTriggerPlugin(TriggerPlugin):
    """Cron 定时触发器插件。"""

    @property
    def trigger_type(self) -> str:
        return "cron"

    async def validate_config(self, config: Dict[str, Any]) -> bool:
        cron_expr = config.get("cron_expression", "")
        parts = cron_expr.strip().split()
        return len(parts) == 5

    async def parse_event(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return raw_data

    async def verify_signature(self, request_data: bytes, headers: Dict[str, str]) -> bool:
        return True
