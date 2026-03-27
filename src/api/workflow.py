"""工作流管理 API"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException
from src.schema import WorkflowCreate, WorkflowUpdate, WorkflowResponse, BaseResponse
from src.dao.orm.model import Workflow

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("", response_model=WorkflowResponse)
async def create_workflow(data: WorkflowCreate):
    """创建工作流"""
    workflow = await Workflow.create(
        name=data.name,
        description=data.description,
        trigger_type=data.trigger_type,
        trigger_config=data.trigger_config,
        actions=data.actions,
    )
    return await WorkflowResponse.from_tortoise_orm(workflow)


@router.get("", response_model=List[WorkflowResponse])
async def list_workflows(status: str = None):
    """列出工作流"""
    query = Workflow.all()
    if status:
        query = query.filter(status=status)
    workflows = await query.all()
    return [await WorkflowResponse.from_tortoise_orm(w) for w in workflows]


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: UUID):
    """获取工作流详情"""
    workflow = await Workflow.get_or_none(id=workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return await WorkflowResponse.from_tortoise_orm(workflow)


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(workflow_id: UUID, data: WorkflowUpdate):
    """更新工作流"""
    workflow = await Workflow.get_or_none(id=workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    update_data = data.model_dump(exclude_unset=True)
    await workflow.update_from_dict(update_data).save()
    return await WorkflowResponse.from_tortoise_orm(workflow)


@router.delete("/{workflow_id}", response_model=BaseResponse)
async def delete_workflow(workflow_id: UUID):
    """删除工作流"""
    workflow = await Workflow.get_or_none(id=workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    await workflow.delete()
    return BaseResponse(success=True, message="Workflow deleted")
