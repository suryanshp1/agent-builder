"""
Workflow CRUD and execution endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel

from app.database import get_db
from app.models.workflow import Workflow
from app.models.user import User, Project
from app.middleware.auth import get_current_active_user, verify_project_access

router = APIRouter()


# Pydantic schemas for workflows
class WorkflowStepCreate(BaseModel):
    name: str
    type: str  # 'single_agent', 'parallel', 'conditional'
    agent_id: Optional[str] = None
    agent_ids: Optional[List[str]] = None
    input_mapping: Optional[Dict[str, str]] = {}
    output_capture: Optional[List[str]] = []
    condition: Optional[Dict[str, Any]] = None
    true_branch: Optional[str] = None
    false_branch: Optional[str] = None


class WorkflowCreate(BaseModel):
    project_id: UUID
    name: str
    description: Optional[str] = None
    trigger_type: str = "manual"
    trigger_config: Optional[Dict[str, Any]] = None
    steps: List[Dict[str, Any]]


class WorkflowResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: Optional[str]
    trigger_type: str
    trigger_config: Optional[Dict[str, Any]]
    steps: List[Dict[str, Any]]
    created_by: UUID
    created_at: Any
    updated_at: Any
    
    class Config:
        from_attributes = True


class WorkflowListResponse(BaseModel):
    workflows: List[WorkflowResponse]
    total: int


@router.get("/", response_model=WorkflowListResponse)
async def list_workflows(
    project_id: UUID = Query(..., description="Project ID to filter workflows"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all workflows in a project
    
    Args:
        project_id: Project UUID
        db: Database session
        current_user: Authenticated user
    
    Returns:
        List of workflows
    """
    # Verify project access
    if not verify_project_access(project_id, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )
    
    workflows = db.query(Workflow).filter(Workflow.project_id == project_id).all()
    
    return WorkflowListResponse(
        workflows=workflows,
        total=len(workflows)
    )


@router.post("/", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow_data: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new workflow
    
    Args:
        workflow_data: Workflow configuration
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Created workflow
    """
    # Verify project access
    if not verify_project_access(workflow_data.project_id, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )
    
    # Create workflow
    new_workflow = Workflow(
        project_id=workflow_data.project_id,
        name=workflow_data.name,
        description=workflow_data.description,
        trigger_type=workflow_data.trigger_type,
        trigger_config=workflow_data.trigger_config,
        steps=workflow_data.steps,
        created_by=current_user.id
    )
    
    db.add(new_workflow)
    db.commit()
    db.refresh(new_workflow)
    
    return new_workflow


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get workflow by ID
    
    Args:
        workflow_id: Workflow UUID
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Workflow object
    """
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    # Verify project access
    if not verify_project_access(workflow.project_id, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this workflow"
        )
    
    return workflow


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: UUID,
    workflow_data: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update workflow configuration
    
    Args:
        workflow_id: Workflow UUID
        workflow_data: Updated workflow data
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Updated workflow
    """
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    # Verify project access
    if not verify_project_access(workflow.project_id, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this workflow"
        )
    
    # Update fields
    workflow.name = workflow_data.name
    workflow.description = workflow_data.description
    workflow.trigger_type = workflow_data.trigger_type
    workflow.trigger_config = workflow_data.trigger_config
    workflow.steps = workflow_data.steps
    
    db.commit()
    db.refresh(workflow)
    
    return workflow


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a workflow
    
    Args:
        workflow_id: Workflow UUID
        db: Database session
        current_user: Authenticated user
    """
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    # Verify project access
    if not verify_project_access(workflow.project_id, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this workflow"
        )
    
    db.delete(workflow)
    db.commit()
    
    return None


@router.post("/{workflow_id}/execute", status_code=status.HTTP_202_ACCEPTED)
async def execute_workflow(
    workflow_id: UUID,
    input_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Execute a workflow asynchronously
    
    Args:
        workflow_id: Workflow UUID
        input_data: Input data for the workflow
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Execution object
    """
    from app.models.execution import Execution
    from app.tasks.agent_tasks import execute_workflow_task
    
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    # Verify project access
    if not verify_project_access(workflow.project_id, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this workflow"
        )
    
    # Create execution record
    execution_id = uuid4()
    new_execution = Execution(
        id=execution_id,
        agent_id=None,
        workflow_id=workflow_id,
        status="pending",
        input_data=input_data,
        executed_by=current_user.id
    )
    
    db.add(new_execution)
    db.commit()
    db.refresh(new_execution)
    
    # Queue workflow execution
    execute_workflow_task.delay(
        workflow_id=str(workflow_id),
        input_data=input_data,
        execution_id=str(execution_id)
    )
    
    return new_execution
