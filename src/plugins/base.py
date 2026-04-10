"""插件基类定义"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ActionResult:
    """动作执行结果"""

    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class TriggerPlugin(ABC):
    """触发器插件基类"""

    @property
    @abstractmethod
    def trigger_type(self) -> str:
        """触发器类型标识"""
        pass

    @abstractmethod
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置是否合法"""
        pass

    @abstractmethod
    async def parse_event(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析事件数据，返回标准化的触发数据"""
        pass

    @abstractmethod
    async def verify_signature(self, request_data: bytes, headers: Dict[str, str]) -> bool:
        """验证 Webhook 签名"""
        pass


class ActionPlugin(ABC):
    """动作插件基类"""

    @property
    @abstractmethod
    def action_type(self) -> str:
        """动作类型标识"""
        pass

    @abstractmethod
    async def execute(self, context: Dict[str, Any], config: Dict[str, Any]) -> ActionResult:
        """执行动作"""
        pass

    @abstractmethod
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置是否合法"""
        pass
