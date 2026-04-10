"""数据模型"""

from tortoise import fields
from tortoise.models import Model


class Workflow(Model):
    """工作流"""

    id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)

    # 触发器配置
    trigger_type = fields.CharField(max_length=50)  # "feishu_bitable", "feishu_approval"
    trigger_config = fields.JSONField()

    # 动作配置
    actions = fields.JSONField()  # List[Dict]

    # 状态
    status = fields.CharField(max_length=20, default="active")  # "active", "paused", "error"

    # 元数据
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    created_by = fields.CharField(max_length=100, null=True)

    class Meta:
        table = "workflow"
        indexes = [("status",), ("trigger_type",)]


class WorkflowExecution(Model):
    """工作流执行记录"""

    id = fields.UUIDField(pk=True)
    workflow_id = fields.UUIDField()

    # 触发数据
    trigger_data = fields.JSONField()

    # 执行状态
    status = fields.CharField(max_length=20)  # "running", "success", "failed", "timeout"
    error_message = fields.TextField(null=True)

    # 时间
    started_at = fields.DatetimeField(auto_now_add=True)
    completed_at = fields.DatetimeField(null=True)

    # 元数据
    execution_time_ms = fields.IntField(null=True)

    class Meta:
        table = "workflow_execution"
        indexes = [("workflow_id",), ("status",), ("started_at",)]


class ActionExecution(Model):
    """动作执行记录"""

    id = fields.UUIDField(pk=True)
    execution_id = fields.UUIDField()

    # 动作信息
    action_type = fields.CharField(max_length=50)
    action_config = fields.JSONField()
    action_index = fields.IntField()

    # 执行状态
    status = fields.CharField(max_length=20)  # "pending", "running", "success", "failed"
    error_message = fields.TextField(null=True)
    retry_count = fields.IntField(default=0)

    # 结果
    result = fields.JSONField(null=True)

    # 时间
    executed_at = fields.DatetimeField(auto_now_add=True)
    completed_at = fields.DatetimeField(null=True)

    class Meta:
        table = "action_execution"
        indexes = [("execution_id",), ("status",)]
