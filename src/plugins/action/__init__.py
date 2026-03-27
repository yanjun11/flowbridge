"""动作插件。"""

from src.plugins.action.feishu_notify import FeishuNotifyAction
from src.plugins.action.wecom_notify import WecomNotifyAction

__all__ = ["WecomNotifyAction", "FeishuNotifyAction"]
