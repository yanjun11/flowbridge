from typing import Any, Dict, Optional

from src.plugins.base import ActionPlugin, ActionResult, TriggerPlugin
from src.service.plugin_manager import PluginManager


class DummyTrigger(TriggerPlugin):
    @property
    def trigger_type(self) -> str:
        return "dummy_trigger"

    async def validate_config(self, config: Dict[str, Any]) -> bool:
        return True

    async def parse_event(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return raw_data

    async def verify_signature(self, request_data: bytes, headers: Dict[str, str]) -> bool:
        return True


class DummyAction(ActionPlugin):
    @property
    def action_type(self) -> str:
        return "dummy_action"

    async def execute(self, context: Dict[str, Any], config: Dict[str, Any]) -> ActionResult:
        return ActionResult(success=True, message="ok")

    async def validate_config(self, config: Dict[str, Any]) -> bool:
        return True


def _reset_plugin_manager_state() -> PluginManager:
    manager = PluginManager()
    manager._triggers.clear()
    manager._actions.clear()
    return manager


def test_plugin_manager_register_and_get_trigger() -> None:
    manager = _reset_plugin_manager_state()
    trigger = DummyTrigger()

    manager.register_trigger(trigger)

    assert manager.get_trigger("dummy_trigger") is trigger
    assert manager.get_trigger("not_exists") is None


def test_plugin_manager_register_and_get_action() -> None:
    manager = _reset_plugin_manager_state()
    action = DummyAction()

    manager.register_action(action)

    assert manager.get_action("dummy_action") is action
    assert manager.get_action("not_exists") is None


def test_plugin_manager_register_all_builtin_plugins() -> None:
    manager = _reset_plugin_manager_state()

    manager.register_all()

    assert manager.get_trigger("feishu_bitable") is not None
    assert manager.get_action("wecom_notify") is not None
    assert manager.get_action("feishu_notify") is not None
    assert manager.get_action("http_request") is not None
