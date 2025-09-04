"""Unit tests for database models."""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from agent_workbench.models.database import (
    AgentConfigModel,
    Base,
    ConversationModel,
    MessageModel,
)


@pytest.fixture(scope="function")
async def async_engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def async_session(async_engine):
    """Create a database session for testing."""
    async_session_factory = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_factory() as session:
        yield session


@pytest.mark.asyncio
async def test_conversation_model_create(async_session):
    """Test creating a conversation."""
    conversation_data = {"user_id": uuid4(), "title": "Test Conversation"}

    conversation = await ConversationModel.create(async_session, **conversation_data)

    assert conversation.id is not None
    assert conversation.user_id == conversation_data["user_id"]
    assert conversation.title == conversation_data["title"]
    assert conversation.created_at is not None
    assert conversation.updated_at is not None


@pytest.mark.asyncio
async def test_conversation_model_get_by_id(async_session):
    """Test getting a conversation by ID."""
    # Create a conversation first
    conversation_data = {"user_id": uuid4(), "title": "Test Conversation"}
    conversation = await ConversationModel.create(async_session, **conversation_data)

    # Get the conversation by ID
    retrieved_conversation = await ConversationModel.get_by_id(
        async_session, conversation.id
    )

    assert retrieved_conversation is not None
    assert retrieved_conversation.id == conversation.id
    assert retrieved_conversation.user_id == conversation.user_id
    assert retrieved_conversation.title == conversation.title


@pytest.mark.asyncio
async def test_conversation_model_get_by_user(async_session):
    """Test getting conversations by user ID."""
    user_id = uuid4()

    # Create multiple conversations for the same user
    conversation_data_1 = {"user_id": user_id, "title": "Test Conversation 1"}
    conversation_data_2 = {"user_id": user_id, "title": "Test Conversation 2"}

    await ConversationModel.create(async_session, **conversation_data_1)
    await ConversationModel.create(async_session, **conversation_data_2)

    # Get conversations by user ID
    conversations = await ConversationModel.get_by_user(async_session, user_id)

    assert len(conversations) == 2
    assert all(conv.user_id == user_id for conv in conversations)


@pytest.mark.asyncio
async def test_conversation_model_update(async_session):
    """Test updating a conversation."""
    # Create a conversation
    conversation_data = {"user_id": uuid4(), "title": "Original Title"}
    conversation = await ConversationModel.create(async_session, **conversation_data)

    # Update the conversation
    update_data = {"title": "Updated Title"}
    updated_conversation = await conversation.update(async_session, **update_data)

    assert updated_conversation.title == "Updated Title"
    # Allow equal timestamps since operations happen quickly
    assert updated_conversation.updated_at >= updated_conversation.created_at


@pytest.mark.asyncio
async def test_conversation_model_delete(async_session):
    """Test deleting a conversation."""
    # Create a conversation
    conversation_data = {"user_id": uuid4(), "title": "Test Conversation"}
    conversation = await ConversationModel.create(async_session, **conversation_data)

    # Delete the conversation
    await conversation.delete(async_session)

    # Try to get the deleted conversation
    retrieved_conversation = await ConversationModel.get_by_id(
        async_session, conversation.id
    )

    assert retrieved_conversation is None


@pytest.mark.asyncio
async def test_message_model_create(async_session):
    """Test creating a message."""
    # Create a conversation first
    conversation_data = {"user_id": uuid4(), "title": "Test Conversation"}
    conversation = await ConversationModel.create(async_session, **conversation_data)

    # Create a message
    message_data = {
        "conversation_id": conversation.id,
        "role": "user",
        "content": "Test message content",
        "metadata_": {"key": "value"},
    }

    message = await MessageModel.create(async_session, **message_data)

    assert message.id is not None
    assert message.conversation_id == conversation.id
    assert message.role == "user"
    assert message.content == "Test message content"
    assert message.metadata_ == {"key": "value"}
    assert message.created_at is not None


@pytest.mark.asyncio
async def test_message_model_get_by_conversation(async_session):
    """Test getting messages by conversation ID."""
    # Create a conversation
    conversation_data = {"user_id": uuid4(), "title": "Test Conversation"}
    conversation = await ConversationModel.create(async_session, **conversation_data)

    # Create multiple messages for the conversation
    message_data_1 = {
        "conversation_id": conversation.id,
        "role": "user",
        "content": "First message",
    }
    message_data_2 = {
        "conversation_id": conversation.id,
        "role": "assistant",
        "content": "Second message",
    }

    await MessageModel.create(async_session, **message_data_1)
    await MessageModel.create(async_session, **message_data_2)

    # Get messages by conversation ID
    messages = await MessageModel.get_by_conversation(async_session, conversation.id)

    assert len(messages) == 2
    assert messages[0].content == "First message"
    assert messages[1].content == "Second message"


@pytest.mark.asyncio
async def test_message_model_get_by_id(async_session):
    """Test getting a message by ID."""
    # Create a conversation
    conversation_data = {"user_id": uuid4(), "title": "Test Conversation"}
    conversation = await ConversationModel.create(async_session, **conversation_data)

    # Create a message
    message_data = {
        "conversation_id": conversation.id,
        "role": "user",
        "content": "Test message",
    }
    message = await MessageModel.create(async_session, **message_data)

    # Get the message by ID
    retrieved_message = await MessageModel.get_by_id(async_session, message.id)

    assert retrieved_message is not None
    assert retrieved_message.id == message.id
    assert retrieved_message.content == message.content


@pytest.mark.asyncio
async def test_agent_config_model_create(async_session):
    """Test creating an agent configuration."""
    config_data = {
        "name": "Test Agent Config",
        "description": "Test configuration for testing",
        "config": {
            "model": "gpt-4",
            "temperature": 0.7,
            "tools": ["web_search", "code_interpreter"],
        },
    }

    agent_config = await AgentConfigModel.create(async_session, **config_data)

    assert agent_config.id is not None
    assert agent_config.name == config_data["name"]
    assert agent_config.description == config_data["description"]
    assert agent_config.config == config_data["config"]
    assert agent_config.created_at is not None
    assert agent_config.updated_at is not None


@pytest.mark.asyncio
async def test_agent_config_model_get_by_id(async_session):
    """Test getting an agent configuration by ID."""
    # Create an agent configuration
    config_data = {"name": "Test Agent Config", "config": {"model": "gpt-4"}}
    agent_config = await AgentConfigModel.create(async_session, **config_data)

    # Get the agent configuration by ID
    retrieved_config = await AgentConfigModel.get_by_id(async_session, agent_config.id)

    assert retrieved_config is not None
    assert retrieved_config.id == agent_config.id
    assert retrieved_config.name == agent_config.name


@pytest.mark.asyncio
async def test_agent_config_model_get_all(async_session):
    """Test getting all agent configurations."""
    # Create multiple agent configurations
    config_data_1 = {"name": "Test Config 1", "config": {"model": "gpt-4"}}
    config_data_2 = {"name": "Test Config 2", "config": {"model": "gpt-3.5-turbo"}}

    await AgentConfigModel.create(async_session, **config_data_1)
    await AgentConfigModel.create(async_session, **config_data_2)

    # Get all agent configurations
    agent_configs = await AgentConfigModel.get_all(async_session)

    assert len(agent_configs) == 2
    config_names = [config.name for config in agent_configs]
    assert "Test Config 1" in config_names
    assert "Test Config 2" in config_names


@pytest.mark.asyncio
async def test_agent_config_model_update(async_session):
    """Test updating an agent configuration."""
    # Create an agent configuration
    config_data = {"name": "Original Name", "config": {"model": "gpt-4"}}
    agent_config = await AgentConfigModel.create(async_session, **config_data)

    # Update the agent configuration
    update_data = {"name": "Updated Name", "description": "Updated description"}
    updated_config = await agent_config.update(async_session, **update_data)

    assert updated_config.name == "Updated Name"
    assert updated_config.description == "Updated description"
    # Allow equal timestamps since operations happen quickly
    assert updated_config.updated_at >= updated_config.created_at


@pytest.mark.asyncio
async def test_agent_config_model_delete(async_session):
    """Test deleting an agent configuration."""
    # Create an agent configuration
    config_data = {"name": "Test Config", "config": {"model": "gpt-4"}}
    agent_config = await AgentConfigModel.create(async_session, **config_data)

    # Delete the agent configuration
    await agent_config.delete(async_session)

    # Try to get the deleted agent configuration
    retrieved_config = await AgentConfigModel.get_by_id(async_session, agent_config.id)

    assert retrieved_config is None
