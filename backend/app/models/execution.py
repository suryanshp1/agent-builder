from sqlalchemy import Column, String, Text, DateTime, Integer, Numeric, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Execution(Base):
    """Execution entity tracking agent/workflow runs"""
    __tablename__ = "executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=True)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=True)
    
    status = Column(String(50), nullable=False, default="pending")
    # Status values: 'pending', 'running', 'success', 'failed', 'cancelled'
    
    input_data = Column(JSONB, nullable=False)
    output_data = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Token and cost tracking
    total_tokens = Column(Integer, default=0)
    total_cost = Column(Numeric(10, 6), default=0.0)  # USD
    
    executed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    agent = relationship("Agent", back_populates="executions")
    workflow = relationship("Workflow", back_populates="executions")
    executed_by_user = relationship("User", back_populates="executions")
    logs = relationship("ExecutionLog", back_populates="execution", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Execution(id={self.id}, status={self.status})>"


class ExecutionLog(Base):
    """Detailed logs for each execution step"""
    __tablename__ = "execution_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("executions.id"), nullable=False, index=True)
    step_number = Column(Integer, nullable=False)
    log_type = Column(String(50), nullable=False)
    # Log types: 'llm_start', 'llm_token', 'llm_end', 'tool_start', 'tool_end', 'error', 'info'
    
    log_data = Column(JSONB, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    execution = relationship("Execution", back_populates="logs")
    
    def __repr__(self):
        return f"<ExecutionLog(id={self.id}, type={self.log_type})>"


# Create composite index for efficient log queries
Index('idx_execution_logs_execution_timestamp', 
      ExecutionLog.execution_id, 
      ExecutionLog.timestamp)
