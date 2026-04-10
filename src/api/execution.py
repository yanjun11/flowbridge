"""执行记录查询 API"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from tortoise import connections

from src.api.auth import verify_api_key
from src.dao.orm.model import ActionExecution, Workflow, WorkflowExecution
from src.schema import (
    ActionExecutionResponse,
    ExecutionResponse,
    ExecutionStatsResponse,
    WorkflowFailureItem,
)

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


@router.get("/stats", response_model=ExecutionStatsResponse)
async def get_execution_stats(
    workflow_id: Optional[UUID] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    _: None = Depends(verify_api_key),
):
    """查询执行统计信息"""
    base_query = WorkflowExecution.all()
    if workflow_id is not None:
        base_query = base_query.filter(workflow_id=workflow_id)
    if start_time is not None:
        base_query = base_query.filter(started_at__gte=start_time)
    if end_time is not None:
        base_query = base_query.filter(started_at__lte=end_time)

    total = await base_query.count()
    success_count = await base_query.filter(status="success").count()
    failed_count = await base_query.filter(status="failed").count()
    timeout_count = await base_query.filter(status="timeout").count()
    running_count = await base_query.filter(status="running").count()
    success_rate = success_count / total * 100 if total > 0 else 0.0

    where_clauses = []
    params = []
    param_index = 1
    if workflow_id is not None:
        where_clauses.append(f"workflow_id = ${param_index}")
        params.append(str(workflow_id))
        param_index += 1
    if start_time is not None:
        where_clauses.append(f"started_at >= ${param_index}")
        params.append(start_time)
        param_index += 1
    if end_time is not None:
        where_clauses.append(f"started_at <= ${param_index}")
        params.append(end_time)

    where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    conn = connections.get("default")

    avg_sql = f"SELECT AVG(execution_time_ms) AS avg_execution_time_ms FROM workflow_execution{where_sql}"
    avg_result = await conn.execute_query_dict(avg_sql, params)
    avg_execution_time_ms = avg_result[0]["avg_execution_time_ms"] if avg_result else None

    failure_filters = ["status IN ('failed', 'timeout')"]
    failure_filters.extend(where_clauses)
    failure_sql = (
        "SELECT workflow_id, COUNT(*) AS failure_count "
        "FROM workflow_execution "
        f"WHERE {' AND '.join(failure_filters)} "
        "GROUP BY workflow_id "
        "ORDER BY failure_count DESC "
        "LIMIT 5"
    )
    failure_result = await conn.execute_query_dict(failure_sql, params)

    failure_top5 = []
    for item in failure_result:
        workflow_uuid = item["workflow_id"] if isinstance(item["workflow_id"], UUID) else UUID(item["workflow_id"])
        workflow = await Workflow.get_or_none(id=workflow_uuid)
        failure_top5.append(
            WorkflowFailureItem(
                workflow_id=workflow_uuid,
                workflow_name=workflow.name if workflow else "",
                failure_count=item["failure_count"],
            )
        )

    return ExecutionStatsResponse(
        total=total,
        success_count=success_count,
        failed_count=failed_count,
        timeout_count=timeout_count,
        running_count=running_count,
        success_rate=success_rate,
        avg_execution_time_ms=avg_execution_time_ms,
        failure_top5=failure_top5,
    )


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
    executions = (
        await WorkflowExecution.filter(workflow_id=workflow_id).order_by("-started_at").offset(offset).limit(limit).all()
    )
    return [await ExecutionResponse.from_tortoise_orm(e) for e in executions]


@router.get("/{execution_id}/actions", response_model=List[ActionExecutionResponse])
async def list_action_executions(
    execution_id: UUID,
    _: None = Depends(verify_api_key),
):
    """查询执行记录的动作执行详情"""
    actions = await ActionExecution.filter(execution_id=execution_id).order_by("action_index").all()
    return [await ActionExecutionResponse.from_tortoise_orm(a) for a in actions]
