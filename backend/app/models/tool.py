from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Tool(Base):
    """Tool entity in the registry"""
    __tablename__ = "tools"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)  # 'research', 'automation', 'communication', 'data'
    type = Column(String(50), nullable=False)  # 'prebuilt', 'custom_python', 'api', 'webhook'
    
    # JSON Schema for inputs and outputs
    input_schema = Column(JSONB, nullable=False)
    output_schema = Column(JSONB, nullable=False)
    
    # Implementation details (code, API URL, etc.)
    implementation = Column(JSONB, nullable=False)
    # Example for API: {"method": "POST", "url": "https://...", "headers": {...}}
    # Example for Python: {"code": "def execute(input):\n    ..."}
    
    # Global tools vs project-specific
    is_global = Column(Boolean, default=True, nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", foreign_keys=[project_id])
    
    def __repr__(self):
        return f"<Tool(id={self.id}, name={self.name}, type={self.type})>"
