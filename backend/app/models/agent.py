from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Agent(Base):
    """Agent entity with configuration"""
    __tablename__ = "agents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(Text, nullable=False)  # Agent persona/role
    goal = Column(Text, nullable=False)  # Agent goal/objective
    instructions = Column(Text)  # System instructions
    
    # Configuration stored as JSONB for flexibility
    configuration = Column(JSONB, nullable=False, default={})
    # Example: {"temperature": 0.7, "max_tokens": 2000, "model": "qwen/qwen-3-72b"}
    
    # Array of tool IDs assigned to this agent
    tool_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False, default=[])
    
    # Memory configuration
    memory_config = Column(JSONB, nullable=False, default={})
    # Example: {"type": "vector", "retention_days": 30, "collection_name": "agent_xyz"}
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="agents")
    created_by_user = relationship("User", back_populates="agents_created")
    executions = relationship("Execution", back_populates="agent")
    
    def __repr__(self):
        return f"<Agent(id={self.id}, name={self.name})>"
