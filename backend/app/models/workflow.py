from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Workflow(Base):
    """Workflow entity for multi-agent orchestration"""
    __tablename__ = "workflows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    trigger_type = Column(String(50), nullable=False, default="manual")
    # Trigger types: 'manual', 'scheduled', 'webhook'
    
    trigger_config = Column(JSONB, nullable=True)
    # Example for scheduled: {"cron": "0 9 * * *", "timezone": "UTC"}
    # Example for webhook: {"url": "...", "secret": "..."}
    
    # Array of step configurations
    steps = Column(JSONB, nullable=False, default=[])
    # Example step: {
    #   "name": "research_step",
    #   "type": "single_agent",
    #   "agent_id": "uuid",
    #   "input_mapping": {...},
    #   "output_capture": ["result"]
    # }
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="workflows")
    created_by_user = relationship("User")
    executions = relationship("Execution", back_populates="workflow")
    
    def __repr__(self):
        return f"<Workflow(id={self.id}, name={self.name})>"
