"""
Agent CRUD endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.agent import Agent
from app.models.user import User, Project
from app.schemas.agent import AgentCreate, AgentResponse, AgentUpdate, AgentListResponse
from app.middleware.auth import get_current_active_user, verify_project_access

router = APIRouter()


@router.get("/", response_model=AgentListResponse)
async def list_agents(
    project_id: UUID = Query(..., description="Project ID to filter agents"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all agents in a project with pagination
    
    Args:
        project_id: UUID of the project
        page: Page number (1-indexed)
        page_size: Number of items per page
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Paginated list of agents
    
    Raises:
        HTTPException: If user doesn't have access to project
    """
    # Verify project access
    if not verify_project_access(project_id, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Query agents
    query = db.query(Agent).filter(Agent.project_id == project_id)
    total = query.count()
    agents = query.offset(offset).limit(page_size).all()
    
    return AgentListResponse(
        agents=agents,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new agent
    
    Args:
        agent_data: Agent configuration data
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Created agent object
    
    Raises:
        HTTPException: If user doesn't have access to project
    """
    # Verify project access
    if not verify_project_access(agent_data.project_id, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )
    
    # Create new agent
    new_agent = Agent(
        project_id=agent_data.project_id,
        name=agent_data.name,
        role=agent_data.role,
        goal=agent_data.goal,
        instructions=agent_data.instructions,
        configuration=agent_data.configuration,
        tool_ids=agent_data.tool_ids,
        memory_config=agent_data.memory_config,
        created_by=current_user.id
    )
    
    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)
    
    return new_agent


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get agent by ID
    
    Args:
        agent_id: Agent UUID
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Agent object
    
    Raises:
        HTTPException: If agent not found or access denied
    """
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Verify project access
    if not verify_project_access(agent.project_id, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this agent"
        )
    
    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: UUID,
    agent_data: AgentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update agent configuration
    
    Args:
        agent_id: Agent UUID
        agent_data: Updated agent data
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Updated agent object
    
    Raises:
        HTTPException: If agent not found or access denied
    """
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Verify project access
    if not verify_project_access(agent.project_id, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this agent"
        )
    
    # Update fields
    update_data = agent_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)
    
    db.commit()
    db.refresh(agent)
    
    return agent


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete an agent
    
    Args:
        agent_id: Agent UUID
        db: Database session
        current_user: Authenticated user
    
    Raises:
        HTTPException: If agent not found or access denied
    """
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Verify project access
    if not verify_project_access(agent.project_id, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this agent"
        )
    
    db.delete(agent)
    db.commit()
    
    return None
