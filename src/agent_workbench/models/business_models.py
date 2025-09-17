"""Business profile and SEO analysis models for seo_coach mode."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .database import Base


class BusinessProfile(BaseModel):
    """Pydantic model for business profile data."""

    id: Optional[UUID] = None
    conversation_id: UUID
    business_name: str = Field(..., min_length=1, max_length=255)
    website_url: str = Field(..., pattern=r"^https?://.+")
    business_type: str = Field(..., max_length=100)
    target_market: str = Field(default="Nederland", max_length=100)
    seo_experience_level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    created_at: Optional[datetime] = None

    @validator("website_url")
    def validate_website_url(cls, v):
        """Validate website URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("Website URL must start with http:// or https://")
        return v


class SEOAnalysisContext(BaseModel):
    """SEO analysis context for coaching recommendations."""

    website_url: str
    analysis_timestamp: datetime
    technical_issues: List[Dict[str, Any]] = []
    content_recommendations: List[str] = []
    priority_score: int = Field(ge=0, le=100)
    recommendations: List[Dict[str, Any]] = []
    llmstxt_analysis: Optional[Dict[str, Any]] = None


class WorkflowExecution(BaseModel):
    """Workflow execution tracking model."""

    id: Optional[UUID] = None
    conversation_id: UUID
    workflow_mode: str
    execution_steps: List[str]
    execution_successful: bool
    error_details: Optional[str] = None
    execution_duration_ms: Optional[int] = None
    created_at: Optional[datetime] = None


# Database models for SQLAlchemy


class BusinessProfileDB(Base):
    """Database model for business profiles."""

    __tablename__ = "business_profiles"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    conversation_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False
    )
    business_name = Column(String(255), nullable=False)
    website_url = Column(String(255), nullable=False)
    business_type = Column(String(100), nullable=False)
    target_market = Column(String(100), default="Nederland")
    seo_experience_level = Column(String(50), default="beginner")
    created_at = Column(DateTime, default=datetime.utcnow)


class WorkflowExecutionDB(Base):
    """Database model for workflow execution tracking."""

    __tablename__ = "workflow_executions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    conversation_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False
    )
    workflow_mode = Column(String(20), nullable=False)
    execution_steps = Column(JSON)
    execution_successful = Column(Boolean, default=True)
    error_details = Column(Text, nullable=True)
    execution_duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
