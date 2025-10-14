"""SQLAlchemy async models for Agent Workbench database."""

from datetime import datetime
from typing import List, Optional, cast
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    select,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship
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
    user_id = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,  # Nullable during migration, will be NOT NULL after
    )
    title = mapped_column(String(255), nullable=True)

    # Relationships
    messages = relationship(
        "MessageModel",
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="select",
    )
    user = relationship("UserModel", back_populates="conversations", lazy="select")

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


class UserModel(Base):
    """SQLAlchemy model for users table (provider-agnostic authentication)."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # Generic authentication fields (provider-agnostic)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    auth_provider: Mapped[str] = mapped_column(
        String(50), default="huggingface", nullable=False
    )

    # Provider-specific data (flexible JSON storage)
    # HuggingFace: {"hf_user_id": "...", "hf_avatar_url": "...", ...}
    # Google: {"google_id": "...", "picture": "...", ...}
    # GitHub: {"github_id": "...", "login": "...", ...}
    provider_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Account metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    last_login: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    conversations: Mapped[List["ConversationModel"]] = relationship(
        "ConversationModel", back_populates="user", lazy="select"
    )
    settings: Mapped[List["UserSettingModel"]] = relationship(
        "UserSettingModel", back_populates="user", cascade="all, delete-orphan", lazy="select"
    )
    sessions: Mapped[List["UserSessionModel"]] = relationship(
        "UserSessionModel", back_populates="user", cascade="all, delete-orphan", lazy="select"
    )

    __table_args__ = (
        Index("idx_users_username", "username"),
        Index("idx_users_provider_email", "auth_provider", "email"),
    )

    @classmethod
    async def create(cls, session: AsyncSession, **kwargs) -> "UserModel":
        """Create a new user."""
        user = cls(**kwargs)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @classmethod
    async def get_by_id(cls, session: AsyncSession, id: UUID) -> Optional["UserModel"]:
        """Get user by ID."""
        result = await session.execute(select(cls).where(cls.id == id))
        scalar_result = result.scalar_one_or_none()
        return cast(Optional["UserModel"], scalar_result)

    @classmethod
    async def get_by_username(
        cls, session: AsyncSession, username: str
    ) -> Optional["UserModel"]:
        """Get user by username."""
        result = await session.execute(select(cls).where(cls.username == username))
        scalar_result = result.scalar_one_or_none()
        return cast(Optional["UserModel"], scalar_result)

    @classmethod
    async def get_by_email(
        cls, session: AsyncSession, email: str, provider: str
    ) -> Optional["UserModel"]:
        """Get user by email and provider."""
        result = await session.execute(
            select(cls).where(cls.email == email, cls.auth_provider == provider)
        )
        scalar_result = result.scalar_one_or_none()
        return cast(Optional["UserModel"], scalar_result)

    async def update(self, session: AsyncSession, **kwargs) -> "UserModel":
        """Update user fields."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        await session.commit()
        await session.refresh(self)
        return self

    async def delete(self, session: AsyncSession) -> None:
        """Delete user."""
        await session.delete(self)
        await session.commit()


class UserSettingModel(Base):
    """SQLAlchemy model for user_settings table (flexible key-value store)."""

    __tablename__ = "user_settings"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    setting_key: Mapped[str] = mapped_column(String(255), nullable=False)
    setting_value: Mapped[dict] = mapped_column(JSON, nullable=False)
    setting_type: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint("setting_type IN ('active', 'passive')"),
        nullable=False,
    )

    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="settings")

    __table_args__ = (
        Index("idx_user_settings_key", "user_id", "setting_key"),
    )

    @classmethod
    async def create(cls, session: AsyncSession, **kwargs) -> "UserSettingModel":
        """Create a new user setting."""
        setting = cls(**kwargs)
        session.add(setting)
        await session.commit()
        await session.refresh(setting)
        return setting

    @classmethod
    async def get_by_user_and_key(
        cls, session: AsyncSession, user_id: UUID, setting_key: str
    ) -> Optional["UserSettingModel"]:
        """Get user setting by user_id and key."""
        result = await session.execute(
            select(cls).where(cls.user_id == user_id, cls.setting_key == setting_key)
        )
        scalar_result = result.scalar_one_or_none()
        return cast(Optional["UserSettingModel"], scalar_result)

    @classmethod
    async def get_by_user(
        cls, session: AsyncSession, user_id: UUID
    ) -> List["UserSettingModel"]:
        """Get all settings for a user."""
        result = await session.execute(select(cls).where(cls.user_id == user_id))
        return list(result.scalars().all())

    async def update(self, session: AsyncSession, **kwargs) -> "UserSettingModel":
        """Update setting fields."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        await session.commit()
        await session.refresh(self)
        return self

    async def delete(self, session: AsyncSession) -> None:
        """Delete user setting."""
        await session.delete(self)
        await session.commit()


class UserSessionModel(Base):
    """SQLAlchemy model for user_sessions table (session tracking)."""

    __tablename__ = "user_sessions"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Session tracking
    session_start: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    session_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_activity: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Request metadata
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    referrer: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Activity tracking
    total_messages: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tool_calls: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="sessions")
    activities: Mapped[List["SessionActivityModel"]] = relationship(
        "SessionActivityModel", back_populates="session", cascade="all, delete-orphan", lazy="select"
    )

    __table_args__ = (
        Index("idx_session_user_activity", "user_id", "last_activity"),
    )

    @classmethod
    async def create(cls, session: AsyncSession, **kwargs) -> "UserSessionModel":
        """Create a new user session."""
        user_session = cls(**kwargs)
        session.add(user_session)
        await session.commit()
        await session.refresh(user_session)
        return user_session

    @classmethod
    async def get_by_id(
        cls, session: AsyncSession, id: UUID
    ) -> Optional["UserSessionModel"]:
        """Get session by ID."""
        result = await session.execute(select(cls).where(cls.id == id))
        scalar_result = result.scalar_one_or_none()
        return cast(Optional["UserSessionModel"], scalar_result)

    @classmethod
    async def get_active_by_user(
        cls, session: AsyncSession, user_id: UUID, since: datetime
    ) -> Optional["UserSessionModel"]:
        """Get active session for user (within timeout window)."""
        result = await session.execute(
            select(cls)
            .where(
                cls.user_id == user_id,
                cls.session_end.is_(None),
                cls.last_activity >= since,
            )
            .order_by(cls.last_activity.desc())
        )
        scalar_result = result.scalar_one_or_none()
        return cast(Optional["UserSessionModel"], scalar_result)

    async def update(self, session: AsyncSession, **kwargs) -> "UserSessionModel":
        """Update session fields."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        await session.commit()
        await session.refresh(self)
        return self

    async def delete(self, session: AsyncSession) -> None:
        """Delete user session."""
        await session.delete(self)
        await session.commit()


class SessionActivityModel(Base):
    """SQLAlchemy model for session_activities table (granular activity logging)."""

    __tablename__ = "session_activities"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("user_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    timestamp: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    session: Mapped["UserSessionModel"] = relationship(
        "UserSessionModel", back_populates="activities"
    )

    __table_args__ = (
        Index("idx_session_activities_session_id", "session_id"),
        Index("idx_session_activities_timestamp", "timestamp"),
    )

    @classmethod
    async def create(cls, session: AsyncSession, **kwargs) -> "SessionActivityModel":
        """Create a new session activity."""
        activity = cls(**kwargs)
        session.add(activity)
        await session.commit()
        await session.refresh(activity)
        return activity

    @classmethod
    async def get_by_session(
        cls, session: AsyncSession, session_id: UUID
    ) -> List["SessionActivityModel"]:
        """Get activities by session ID."""
        result = await session.execute(
            select(cls).where(cls.session_id == session_id).order_by(cls.timestamp)
        )
        return list(result.scalars().all())

    async def delete(self, session: AsyncSession) -> None:
        """Delete session activity."""
        await session.delete(self)
        await session.commit()
