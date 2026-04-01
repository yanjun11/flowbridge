"""执行记录查询 API"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from src.schema import ExecutionResponse, ActionExecutionResponse
from src.dao.orm.model import WorkflowExecution, ActionExecution
from src.api.auth import verify_api_key

router = APIRouter(prefix="/executions", tags=["executions"])


@router.get("", response_model=List[ExecutionResponse])
async def list_executions(
    status: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    _: None = Depends(verify_api_key),
):
    """查询执行记录列表"""
    query = WorkflowExecution.all()
    if status is not None:
        query = query.filter(status=status)

    executions = await query.order_by("-started_at").offset(offset).limit(limit).all()
    return [await ExecutionResponse.from_tortoise_orm(e) for e in executions]


@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(execution_id: UUID, _: None = Depends(verify_api_key)):
    """获取执行记录详情"""
    execution = await WorkflowExecution.get_or_none(id=execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return await ExecutionResponse.from_tortoise_orm(execution)


@router.get("/workflow/{workflow_id}", response_model=List[ExecutionResponse])
async def list_workflow_executions(
    workflow_id: UUID,
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    _: None = Depends(verify_api_key),
):
    """查询工作流的执行历史"""
    executions = await WorkflowExecution.filter(
        workflow_id=workflow_id
    ).order_by("-started_at").offset(offset).limit(limit).all()
    return [await ExecutionResponse.from_tortoise_orm(e) for e in executions]


@router.get("/{execution_id}/actions", response_model=List[ActionExecutionResponse])
async def list_action_executions(
    execution_id: UUID,
    _: None = Depends(verify_api_key),
):
    """查询执行记录的动作执行详情"""
    actions = await ActionExecution.filter(
        execution_id=execution_id
    ).order_by("action_index").all()
    return [await ActionExecutionResponse.from_tortoise_orm(a) for a in actions]
