"""模板渲染工具"""
import html
import re
from typing import Any, Dict


def render_template(template: str, context: Dict[str, Any]) -> str:
    """
    渲染模板，支持 {{variable}} 语法

    示例:
        template = "Hello {{trigger.name}}, amount: {{trigger.amount}}"
        context = {"trigger": {"name": "Alice", "amount": 100}}
        result = "Hello Alice, amount: 100"
    """
    if not template:
        return ""

    def replace_var(match):
        var_path = match.group(1).strip()
        value = _get_nested_value(context, var_path)
        return html.escape(str(value), quote=True) if value is not None else ""

    return re.sub(r"\{\{([^}]+)\}\}", replace_var, template)


def _get_nested_value(data: Dict[str, Any], path: str) -> Any:
    """获取嵌套字段值，支持 a.b.c 语法"""
    keys = path.split(".")
    value = data

    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return None

        if value is None:
            return None

    return value
