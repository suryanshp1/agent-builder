"""
Authentication middleware and dependencies
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.utils.auth import verify_token
from app.schemas.user import TokenData

# HTTP Bearer token security
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token
    
    Args:
        credentials: HTTP Authorization header with Bearer token
        db: Database session
    
    Returns:
        Current User object
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials:
        raise credentials_exception
    
    token = credentials.credentials
    
    # Verify token
    token_data = verify_token(token, token_type="access")
    if token_data is None:
        raise credentials_exception
    
    # Get user from database
    user = db.query(User).filter(User.id == token_data.user_id).first()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure user is active
    
    Args:
        current_user: Current user from get_current_user
    
    Returns:
        Active User object
    
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure user has admin role
    
    Args:
        current_user: Current user from get_current_user
    
    Returns:
        Admin User object
    
    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def verify_project_access(project_id: UUID, user: User, db: Session) -> bool:
    """
    Verify user has access to a specific project
    
    Args:
        project_id: Project UUID
        user: User object
        db: Database session
    
    Returns:
        True if user has access, False otherwise
    """
    from app.models.user import Project
    
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == user.organization_id
    ).first()
    
    return project is not None


def verify_agent_access(agent_id: UUID, user: User, db: Session) -> bool:
    """
    Verify user has access to a specific agent
    
    Args:
        agent_id: Agent UUID
        user: User object
        db: Database session
    
    Returns:
        True if user has access, False otherwise
    """
    from app.models.agent import Agent
    from app.models.user import Project
    
    agent = db.query(Agent).join(Project).filter(
        Agent.id == agent_id,
        Project.organization_id == user.organization_id
    ).first()
    
    return agent is not None
