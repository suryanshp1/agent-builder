from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from uuid import UUID


class AgentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., min_length=1)
    goal: str = Field(..., min_length=1)
    instructions: Optional[str] = None


class AgentCreate(AgentBase):
    project_id: UUID
    configuration: Dict[str, Any] = Field(default_factory=lambda: {
        "temperature": 0.7,
        "max_tokens": 2000,
        "model": "qwen/qwen-3-72b"
    })
    tool_ids: List[UUID] = Field(default_factory=list)
    memory_config: Dict[str, Any] = Field(default_factory=lambda: {
        "type": "session",
        "retention_days": 7
    })


class AgentResponse(AgentBase):
    id: UUID
    project_id: UUID
    configuration: Dict[str, Any]
    tool_ids: List[UUID]
    memory_config: Dict[str, Any]
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[str] = None
    goal: Optional[str] = None
    instructions: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    tool_ids: Optional[List[UUID]] = None
    memory_config: Optional[Dict[str, Any]] = None


class AgentListResponse(BaseModel):
    agents: List[AgentResponse]
    total: int
    page: int
    page_size: int
