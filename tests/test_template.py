from src.service.template import render_template


def test_render_template_variable_replacement() -> None:
    template = "Hello {{name}}"
    context = {"name": "Alice"}

    assert render_template(template, context) == "Hello Alice"


def test_render_template_nested_field() -> None:
    template = "Order {{trigger.order.id}} amount={{trigger.order.amount}}"
    context = {"trigger": {"order": {"id": "ORD-001", "amount": 99}}}

    assert render_template(template, context) == "Order ORD-001 amount=99"


def test_render_template_missing_field_returns_empty_string() -> None:
    template = "Hello {{name}}, phone={{user.phone}}"
    context = {"name": "Alice", "user": {}}

    assert render_template(template, context) == "Hello Alice, phone="
