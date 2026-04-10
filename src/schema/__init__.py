"""Pydantic Schema 定义"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """基础响应"""

    success: bool
    message: str = ""
    data: Optional[Any] = None


class WorkflowCreate(BaseModel):
    """创建工作流"""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    trigger_type: str = Field(..., min_length=1)
    trigger_config: Dict[str, Any]
    actions: List[Dict[str, Any]]


class WorkflowUpdate(BaseModel):
    """更新工作流"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    trigger_config: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None


class WorkflowResponse(BaseModel):
    """工作流响应"""

    id: UUID
    name: str
    description: Optional[str]
    trigger_type: str
    trigger_config: Dict[str, Any]
    actions: List[Dict[str, Any]]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExecutionResponse(BaseModel):
    """执行记录响应"""

    id: UUID
    workflow_id: UUID
    trigger_data: Dict[str, Any]
    status: str
    error_message: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    execution_time_ms: Optional[int]

    class Config:
        from_attributes = True


class ActionExecutionResponse(BaseModel):
    """动作执行记录响应"""

    id: UUID
    execution_id: UUID
    action_type: str
    action_config: Dict[str, Any]
    action_index: int
    status: str
    error_message: Optional[str]
    retry_count: int
    result: Optional[Dict[str, Any]]
    executed_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class WorkflowFailureItem(BaseModel):
    """失败排行项"""

    workflow_id: UUID
    workflow_name: str
    failure_count: int


class ExecutionStatsResponse(BaseModel):
    """执行统计响应"""

    total: int
    success_count: int
    failed_count: int
    timeout_count: int
    running_count: int
    success_rate: float
    avg_execution_time_ms: Optional[float]
    failure_top5: List[WorkflowFailureItem]
