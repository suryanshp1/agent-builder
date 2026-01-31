from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class ExecutionBase(BaseModel):
    input_data: Dict[str, Any]


class ExecutionCreate(ExecutionBase):
    agent_id: Optional[UUID] = None
    workflow_id: Optional[UUID] = None


class ExecutionLogResponse(BaseModel):
    id: UUID
    execution_id: UUID
    step_number: int
    log_type: str
    log_data: Dict[str, Any]
    timestamp: datetime
    
    class Config:
        from_attributes = True


class ExecutionResponse(ExecutionBase):
    id: UUID
    agent_id: Optional[UUID]
    workflow_id: Optional[UUID]
    status: str
    output_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    total_tokens: int
    total_cost: Decimal
    executed_by: UUID
    
    class Config:
        from_attributes = True


class ExecutionDetailResponse(ExecutionResponse):
    logs: List[ExecutionLogResponse] = []


class ExecutionListResponse(BaseModel):
    executions: List[ExecutionResponse]
    total: int
    page: int
    page_size: int
