from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from uuid import UUID


class ToolBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    category: str = Field(..., pattern="^(research|automation|communication|data)$")
    type: str = Field(..., pattern="^(prebuilt|custom_python|api|webhook)$")


class ToolCreate(ToolBase):
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    implementation: Dict[str, Any]
    is_global: bool = True
    project_id: Optional[UUID] = None


class ToolResponse(ToolBase):
    id: UUID
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    implementation: Dict[str, Any]
    is_global: bool
    project_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ToolUpdate(BaseModel):
    description: Optional[str] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    implementation: Optional[Dict[str, Any]] = None


class ToolListResponse(BaseModel):
    tools: List[ToolResponse]
    total: int
