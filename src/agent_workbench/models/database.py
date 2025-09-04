"""SQLAlchemy async models for Agent Workbench database."""

from typing import List, Optional, cast
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    select,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.sql import func

Base: DeclarativeMeta = declarative_base()


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )


class ConversationModel(Base, TimestampMixin):
    """SQLAlchemy model for conversations table."""

    __tablename__ = "conversations"

    id = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    # Future: for multi-user support
    user_id = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    title = mapped_column(String(255), nullable=True)

    # Relationships
    messages = relationship(
        "MessageModel",
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="select",
    )

    __table_args__ = (Index("idx_conversations_user_id", "user_id"),)

    @classmethod
    async def create(cls, session: AsyncSession, **kwargs) -> "ConversationModel":
        """Create a new conversation."""
        conversation = cls(**kwargs)
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)
        return conversation

    @classmethod
    async def get_by_id(
        cls, session: AsyncSession, id: UUID
    ) -> Optional["ConversationModel"]:
        """Get conversation by ID."""
        result = await session.execute(select(cls).where(cls.id == id))
        scalar_result = result.scalar_one_or_none()
        return cast(Optional["ConversationModel"], scalar_result)

    @classmethod
    async def get_by_user(
        cls, session: AsyncSession, user_id: UUID
    ) -> List["ConversationModel"]:
        """Get conversations by user ID."""
        result = await session.execute(select(cls).where(cls.user_id == user_id))
        return list(result.scalars().all())

    async def update(self, session: AsyncSession, **kwargs) -> "ConversationModel":
        """Update conversation fields."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        await session.commit()
        await session.refresh(self)
        return self

    async def delete(self, session: AsyncSession) -> None:
        """Delete conversation."""
        await session.delete(self)
        await session.commit()


class MessageModel(Base):
    """SQLAlchemy model for messages table."""

    __tablename__ = "messages"

    id = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    role = mapped_column(
        String(20),
        CheckConstraint("role IN ('user', 'assistant', 'tool', 'system')"),
        nullable=False,
    )
    content = mapped_column(Text, nullable=False)
    metadata_ = mapped_column("metadata", JSON, nullable=True)
    created_at = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relationships
    conversation = relationship("ConversationModel", back_populates="messages")

    __table_args__ = (
        Index("idx_messages_conversation_id", "conversation_id"),
        Index("idx_messages_created_at", "created_at"),
    )

    @classmethod
    async def create(cls, session: AsyncSession, **kwargs) -> "MessageModel":
        """Create a new message."""
        message = cls(**kwargs)
        session.add(message)
        await session.commit()
        await session.refresh(message)
        return message

    @classmethod
    async def get_by_conversation(
        cls, session: AsyncSession, conversation_id: UUID
    ) -> List["MessageModel"]:
        """Get messages by conversation ID."""
        result = await session.execute(
            select(cls)
            .where(cls.conversation_id == conversation_id)
            .order_by(cls.created_at)
        )
        return list(result.scalars().all())

    @classmethod
    async def get_by_id(
        cls, session: AsyncSession, id: UUID
    ) -> Optional["MessageModel"]:
        """Get message by ID."""
        result = await session.execute(select(cls).where(cls.id == id))
        scalar_result = result.scalar_one_or_none()
        return cast(Optional["MessageModel"], scalar_result)

    async def update(self, session: AsyncSession, **kwargs) -> "MessageModel":
        """Update message fields."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        await session.commit()
        await session.refresh(self)
        return self

    async def delete(self, session: AsyncSession) -> None:
        """Delete message."""
        await session.delete(self)
        await session.commit()


class AgentConfigModel(Base, TimestampMixin):
    """SQLAlchemy model for agent configurations table."""

    __tablename__ = "agent_configs"

    id = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = mapped_column(String(255), nullable=False)
    description = mapped_column(Text, nullable=True)
    config = mapped_column(JSON, nullable=False)

    __table_args__ = (Index("idx_agent_configs_name", "name"),)

    @classmethod
    async def create(cls, session: AsyncSession, **kwargs) -> "AgentConfigModel":
        """Create a new agent configuration."""
        agent_config = cls(**kwargs)
        session.add(agent_config)
        await session.commit()
        await session.refresh(agent_config)
        return agent_config

    @classmethod
    async def get_by_id(
        cls, session: AsyncSession, id: UUID
    ) -> Optional["AgentConfigModel"]:
        """Get agent configuration by ID."""
        result = await session.execute(select(cls).where(cls.id == id))
        scalar_result = result.scalar_one_or_none()
        return cast(Optional["AgentConfigModel"], scalar_result)

    @classmethod
    async def get_all(cls, session: AsyncSession) -> List["AgentConfigModel"]:
        """Get all agent configurations."""
        result = await session.execute(select(cls))
        return list(result.scalars().all())

    async def update(self, session: AsyncSession, **kwargs) -> "AgentConfigModel":
        """Update agent configuration fields."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        await session.commit()
        await session.refresh(self)
        return self

    async def delete(self, session: AsyncSession) -> None:
        """Delete agent configuration."""
        await session.delete(self)
        await session.commit()
