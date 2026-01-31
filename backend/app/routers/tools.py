"""
Tool Registry CRUD endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.models.tool import Tool
from app.models.user import User
from app.schemas.tool import ToolCreate, ToolResponse, ToolUpdate, ToolListResponse
from app.middleware.auth import get_current_active_user

router = APIRouter()


@router.get("/", response_model=ToolListResponse)
async def list_tools(
    category: Optional[str] = Query(None, description="Filter by category"),
    type: Optional[str] = Query(None, description="Filter by type"),
    project_id: Optional[UUID] = Query(None, description="Filter by project (includes global tools)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all available tools (global + project-specific)
    
    Args:
        category: Optional category filter
        type: Optional type filter
        project_id: Optional project filter
        db: Database session
        current_user: Authenticated user
    
    Returns:
        List of tools
    """
    # Base query - global tools or user's organization project tools
    query = db.query(Tool).filter(
        (Tool.is_global == True) |
        (Tool.project_id.in_(
            db.query(Tool.project_id).join(Tool.project).filter(
                Tool.project.has(organization_id=current_user.organization_id)
            )
        ))
    )
    
    # Apply filters
    if category:
        query = query.filter(Tool.category == category)
    
    if type:
        query = query.filter(Tool.type == type)
    
    if project_id:
        query = query.filter(
            (Tool.is_global == True) | (Tool.project_id == project_id)
        )
    
    tools = query.all()
    
    return ToolListResponse(
        tools=tools,
        total=len(tools)
    )


@router.post("/", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
async def create_tool(
    tool_data: ToolCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new custom tool
    
    Args:
        tool_data: Tool configuration data
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Created tool object
    
    Raises:
        HTTPException: If tool name already exists or validation fails
    """
    # Check if tool name already exists
    existing_tool = db.query(Tool).filter(Tool.name == tool_data.name).first()
    if existing_tool:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tool with name '{tool_data.name}' already exists"
        )
    
    # Create new tool
    new_tool = Tool(
        name=tool_data.name,
        description=tool_data.description,
        category=tool_data.category,
        type=tool_data.type,
        input_schema=tool_data.input_schema,
        output_schema=tool_data.output_schema,
        implementation=tool_data.implementation,
        is_global=tool_data.is_global,
        project_id=tool_data.project_id
    )
    
    db.add(new_tool)
    db.commit()
    db.refresh(new_tool)
    
    return new_tool


@router.get("/{tool_id}", response_model=ToolResponse)
async def get_tool(
    tool_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get tool by ID
    
    Args:
        tool_id: Tool UUID
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Tool object
    
    Raises:
        HTTPException: If tool not found or access denied
    """
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )
    
    # Check access (global tools or same organization)
    if not tool.is_global and tool.project_id:
        project = tool.project
        if project.organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tool"
            )
    
    return tool


@router.put("/{tool_id}", response_model=ToolResponse)
async def update_tool(
    tool_id: UUID,
    tool_data: ToolUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update custom tool (global tools cannot be modified)
    
    Args:
        tool_id: Tool UUID
        tool_data: Updated tool data
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Updated tool object
    
    Raises:
        HTTPException: If tool not found, is global, or access denied
    """
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )
    
    # Cannot modify global tools
    if tool.is_global:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify global tools"
        )
    
    # Check access
    if tool.project_id:
        project = tool.project
        if project.organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tool"
            )
    
    # Update fields
    update_data = tool_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tool, field, value)
    
    db.commit()
    db.refresh(tool)
    
    return tool


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool(
    tool_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a custom tool (global tools cannot be deleted)
    
    Args:
        tool_id: Tool UUID
        db: Database session
        current_user: Authenticated user
    
    Raises:
        HTTPException: If tool not found, is global, or access denied
    """
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )
    
    # Cannot delete global tools
    if tool.is_global:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete global tools"
        )
    
    # Check access
    if tool.project_id:
        project = tool.project
        if project.organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tool"
            )
    
    db.delete(tool)
    db.commit()
    
    return None
