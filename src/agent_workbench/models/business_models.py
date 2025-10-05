"""Business profile and SEO analysis models for seo_coach mode."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator
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

    id: Optional[UUID] = Field(
        None,
        examples=["850e8400-e29b-41d4-a716-446655440003"],
    )
    conversation_id: UUID = Field(
        ...,
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    business_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        examples=["Acme Marketing Agency", "Tech Startup Inc", "Local Bakery"],
    )
    website_url: str = Field(
        ...,
        pattern=r"^https?://.+",
        examples=["https://example.com", "https://mybusiness.nl"],
    )
    business_type: str = Field(
        ...,
        max_length=100,
        examples=["E-commerce", "SaaS", "Local Service", "Content Creator"],
    )
    target_market: str = Field(
        default="Nederland",
        max_length=100,
        examples=["Nederland", "Global", "Europe", "North America"],
    )
    seo_experience_level: Literal["beginner", "intermediate", "advanced"] = Field(
        default="beginner",
        examples=["beginner", "intermediate", "advanced"],
    )
    created_at: Optional[datetime] = Field(
        None,
        examples=["2025-01-05T09:00:00Z"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                "business_name": "Acme Marketing Agency",
                "website_url": "https://acmemarketing.com",
                "business_type": "Marketing Agency",
                "target_market": "Nederland",
                "seo_experience_level": "intermediate",
            }
        }
    )

    @field_validator("website_url")
    @classmethod
    def validate_website_url(cls, v: str) -> str:
        """Validate website URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("Website URL must start with http:// or https://")
        return v


class SEOAnalysisContext(BaseModel):
    """SEO analysis context for coaching recommendations."""

    website_url: str = Field(
        ...,
        examples=["https://example.com"],
    )
    analysis_timestamp: datetime = Field(
        ...,
        examples=["2025-01-05T14:30:00Z"],
    )
    technical_issues: List[Dict[str, Any]] = Field(
        default_factory=list,
        examples=[[{"issue": "Missing meta description", "severity": "medium"}]],
    )
    content_recommendations: List[str] = Field(
        default_factory=list,
        examples=[["Add keyword-rich headings", "Improve internal linking"]],
    )
    priority_score: int = Field(
        ...,
        ge=0,
        le=100,
        examples=[75, 85, 60],
    )
    recommendations: List[Dict[str, Any]] = Field(
        default_factory=list,
        examples=[[{"action": "Optimize page speed", "impact": "high"}]],
    )
    llmstxt_analysis: Optional[Dict[str, Any]] = Field(
        None,
        examples=[{"found": True, "quality_score": 8}],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "website_url": "https://example.com",
                "analysis_timestamp": "2025-01-05T14:30:00Z",
                "technical_issues": [{"issue": "Missing sitemap", "severity": "high"}],
                "content_recommendations": ["Add FAQ section", "Create blog content"],
                "priority_score": 78,
                "recommendations": [{"action": "Fix broken links", "impact": "medium"}],
            }
        }
    )


class WorkflowExecution(BaseModel):
    """Workflow execution tracking model."""

    id: Optional[UUID] = Field(
        None,
        examples=["950e8400-e29b-41d4-a716-446655440004"],
    )
    conversation_id: UUID = Field(
        ...,
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    workflow_mode: str = Field(
        ...,
        examples=["workbench", "seo_coach"],
    )
    execution_steps: List[str] = Field(
        ...,
        examples=[["init", "process_message", "generate_response", "cleanup"]],
    )
    execution_successful: bool = Field(
        ...,
        examples=[True, False],
    )
    error_details: Optional[str] = Field(
        None,
        examples=["LLM timeout error", "Invalid configuration"],
    )
    execution_duration_ms: Optional[int] = Field(
        None,
        examples=[1500, 3200, 850],
    )
    created_at: Optional[datetime] = Field(
        None,
        examples=["2025-01-05T12:15:00Z"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                "workflow_mode": "workbench",
                "execution_steps": ["init", "process_message", "generate_response"],
                "execution_successful": True,
                "execution_duration_ms": 1850,
            }
        }
    )


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
