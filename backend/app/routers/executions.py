"""
Execution endpoints for running agents and viewing results
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID, uuid4

from app.database import get_db
from app.models.execution import Execution
from app.models.user import User
from app.schemas.execution import (
    ExecutionCreate, 
    ExecutionResponse, 
    ExecutionDetailResponse,
    ExecutionListResponse
)
from app.middleware.auth import get_current_active_user, verify_agent_access
from app.tasks.agent_tasks import execute_agent_task

router = APIRouter()


@router.post("/agent/{agent_id}", response_model=ExecutionResponse, status_code=status.HTTP_202_ACCEPTED)
async def execute_agent(
    agent_id: UUID,
    execution_data: ExecutionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Execute an agent asynchronously
    
    Args:
        agent_id: Agent UUID to execute
        execution_data: Input data for the agent
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Execution object with pending status
    
    Raises:
        HTTPException: If agent not found or access denied
    """
    # Verify agent access
    if not verify_agent_access(agent_id, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this agent"
        )
    
    # Create execution record
    execution_id = uuid4()
    new_execution = Execution(
        id=execution_id,
        agent_id=agent_id,
        workflow_id=None,
        status="pending",
        input_data=execution_data.input_data,
        executed_by=current_user.id
    )
    
    db.add(new_execution)
    db.commit()
    db.refresh(new_execution)
    
    # Queue agent execution as Celery task
    execute_agent_task.delay(
        agent_id=str(agent_id),
        input_data=execution_data.input_data,
        execution_id=str(execution_id)
    )
    
    return new_execution


@router.get("/{execution_id}", response_model=ExecutionDetailResponse)
async def get_execution(
    execution_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get execution details with logs
    
    Args:
        execution_id: Execution UUID
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Execution object with logs
    
    Raises:
        HTTPException: If execution not found or access denied
    """
    execution = db.query(Execution).filter(Execution.id == execution_id).first()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )
    
    # Verify access (user's organization or own execution)
    if execution.executed_by != current_user.id:
        # Check if same organization via agent
        if execution.agent_id:
            if not verify_agent_access(execution.agent_id, current_user, db):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this execution"
                )
    
    return execution


@router.get("/", response_model=ExecutionListResponse)
async def list_executions(
    agent_id: Optional[UUID] = Query(None, description="Filter by agent"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List executions with pagination and filtering
    
    Args:
        agent_id: Optional agent filter
        status: Optional status filter
        page: Page number
        page_size: Items per page
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Paginated list of executions
    """
    # Base query - user's executions or organization's executions
    query = db.query(Execution).filter(
        Execution.executed_by == current_user.id
    )
    
    # Apply filters
    if agent_id:
        # Verify access to agent
        if not verify_agent_access(agent_id, current_user, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this agent"
            )
        query = query.filter(Execution.agent_id == agent_id)
    
    if status:
        query = query.filter(Execution.status == status)
    
    # Calculate pagination
    offset = (page - 1) * page_size
    total = query.count()
    executions = query.order_by(Execution.started_at.desc()).offset(offset).limit(page_size).all()
    
    return ExecutionListResponse(
        executions=executions,
        total=total,
        page=page,
        page_size=page_size
    )


@router.delete("/{execution_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_execution(
    execution_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete an execution and its logs
    
    Args:
        execution_id: Execution UUID
        db: Database session
        current_user: Authenticated user
    
    Raises:
        HTTPException: If execution not found or access denied
    """
    execution = db.query(Execution).filter(Execution.id == execution_id).first()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )
    
    # Only owner can delete
    if execution.executed_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this execution"
        )
    
    db.delete(execution)
    db.commit()
    
    return None
