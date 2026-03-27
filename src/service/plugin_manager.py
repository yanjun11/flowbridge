"""插件管理器。"""
from __future__ import annotations

import logging
from typing import Dict, Optional

from src.plugins.base import ActionPlugin, TriggerPlugin
from src.plugins.trigger.feishu_bitable import FeishuBitableTrigger
from src.plugins.action.feishu_notify import FeishuNotifyAction
from src.plugins.action.http_request import HttpRequestAction
from src.plugins.action.wecom_notify import WecomNotifyAction

logger = logging.getLogger(__name__)


class PluginManager:
    """管理 Trigger / Action 插件的单例。"""

    _instance: "PluginManager | None" = None

    def __new__(cls) -> "PluginManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._triggers = {}
            cls._instance._actions = {}
        return cls._instance

    def register_trigger(self, plugin: TriggerPlugin) -> None:
        """注册触发器插件。"""
        self._triggers[plugin.trigger_type] = plugin
        logger.info("Registered trigger plugin: %s", plugin.trigger_type)

    def register_action(self, plugin: ActionPlugin) -> None:
        """注册动作插件。"""
        self._actions[plugin.action_type] = plugin
        logger.info("Registered action plugin: %s", plugin.action_type)

    def get_trigger(self, trigger_type: str) -> Optional[TriggerPlugin]:
        """按类型查找触发器插件。"""
        return self._triggers.get(trigger_type)

    def get_action(self, action_type: str) -> Optional[ActionPlugin]:
        """按类型查找动作插件。"""
        return self._actions.get(action_type)

    def register_all(self) -> None:
        """注册内置插件。"""
        if "feishu_bitable" not in self._triggers:
            self.register_trigger(FeishuBitableTrigger())
        if "wecom_notify" not in self._actions:
            self.register_action(WecomNotifyAction())
        if "feishu_notify" not in self._actions:
            self.register_action(FeishuNotifyAction())
        if "http_request" not in self._actions:
            self.register_action(HttpRequestAction())

    _triggers: Dict[str, TriggerPlugin]
    _actions: Dict[str, ActionPlugin]
