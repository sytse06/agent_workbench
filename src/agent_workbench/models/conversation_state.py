"""Conversation state models and database schemas."""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .database import Base


class ConversationStateDB(Base):
    """Database model for conversation states."""

    __tablename__ = "conversation_states"

    conversation_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("conversations.id"), primary_key=True
    )
    state_data = Column(JSON, nullable=False)
    context_data = Column(JSON)
    active_contexts = Column(JSON)
    updated_at = Column(DateTime, default=datetime.utcnow)
    version = Column(Integer, default=1)
