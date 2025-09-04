"""Integration tests for database operations."""

from uuid import uuid4

import pytest
import pytest_asyncio

from agent_workbench.api.database import DatabaseManager
from agent_workbench.models.config import DatabaseConfig
from agent_workbench.models.database import (
    AgentConfigModel,
    ConversationModel,
    MessageModel,
)


@pytest_asyncio.fixture(scope="function")
async def database_manager():
    """Create a database manager with in-memory SQLite for testing."""
    config = DatabaseConfig(database_url="sqlite+aiosqlite:///:memory:", echo_sql=False)
    db_manager = DatabaseManager(config)
    await db_manager.initialize()
    await db_manager.create_tables()

    yield db_manager

    await db_manager.close()


@pytest.fixture
async def db_session(database_manager):
    """Create a database session for testing."""
    async for session in database_manager.get_session():
        yield session


@pytest.mark.asyncio
async def test_database_manager_initialization():
    """Test database manager initialization."""
    config = DatabaseConfig(database_url="sqlite+aiosqlite:///:memory:", echo_sql=False)
    db_manager = DatabaseManager(config)

    # Should be able to initialize without errors
    await db_manager.initialize()
    assert db_manager.engine is not None
    assert db_manager.session_factory is not None

    # Should be able to initialize again without errors
    await db_manager.initialize()

    await db_manager.close()


@pytest.mark.asyncio
async def test_conversation_lifecycle(database_manager):
    """Test complete conversation lifecycle."""
    async for session in database_manager.get_session():
        # Create conversation
        user_id = uuid4()
        conversation_data = {
            "user_id": user_id,
            "title": "Integration Test Conversation",
        }

        conversation = await ConversationModel.create(session, **conversation_data)
        assert conversation.id is not None
        assert conversation.user_id == user_id
        assert conversation.title == "Integration Test " "Conversation"

        # Retrieve conversation
        retrieved_conversation = await ConversationModel.get_by_id(
            session, conversation.id
        )
        assert retrieved_conversation is not None
        assert retrieved_conversation.id == conversation.id

        # Update conversation
        updated_conversation = await conversation.update(
            session, title="Updated Test Conversation"
        )
        assert updated_conversation.title == "Updated Test Conversation"

        # Delete conversation
        await conversation.delete(session)

        # Verify deletion
        deleted_conversation = await ConversationModel.get_by_id(
            session, conversation.id
        )
        assert deleted_conversation is None


@pytest.mark.asyncio
async def test_message_lifecycle(database_manager):
    """Test complete message lifecycle."""
    async for session in database_manager.get_session():
        # Create conversation first
        conversation = await ConversationModel.create(
            session, user_id=uuid4(), title="Test Conversation for Messages"
        )

        # Create message
        message_data = {
            "conversation_id": conversation.id,
            "role": "user",
            "content": "Test message content for integration",
            "metadata_": {"test": "value"},
        }

        message = await MessageModel.create(session, **message_data)
        assert message.id is not None
        assert message.conversation_id == conversation.id
        assert message.role == "user"
        assert message.content == "Test message content for integration"

        # Retrieve message
        retrieved_message = await MessageModel.get_by_id(session, message.id)
        assert retrieved_message is not None
        assert retrieved_message.id == message.id

        # Get messages by conversation
        messages = await MessageModel.get_by_conversation(session, conversation.id)
        assert len(messages) == 1
        assert messages[0].id == message.id

        # Update message
        updated_message = await message.update(
            session, content="Updated message content"
        )
        assert updated_message.content == "Updated message content"

        # Delete message
        await message.delete(session)

        # Verify deletion
        deleted_message = await MessageModel.get_by_id(session, message.id)
        assert deleted_message is None


@pytest.mark.asyncio
async def test_agent_config_lifecycle(database_manager):
    """Test complete agent configuration lifecycle."""
    async for session in database_manager.get_session():
        # Create agent configuration
        config_data = {
            "name": "Integration Test Config",
            "description": "Test configuration for integration testing",
            "config": {"model": "gpt-4", "temperature": 0.7, "max_tokens": 1000},
        }

        agent_config = await AgentConfigModel.create(session, **config_data)
        assert agent_config.id is not None
        assert agent_config.name == "Integration Test Config"
        assert agent_config.config["model"] == "gpt-4"

        # Retrieve agent configuration
        retrieved_config = await AgentConfigModel.get_by_id(session, agent_config.id)
        assert retrieved_config is not None
        assert retrieved_config.id == agent_config.id

        # Get all configurations
        all_configs = await AgentConfigModel.get_all(session)
        assert len(all_configs) == 1
        assert all_configs[0].id == agent_config.id

        # Update agent configuration
        updated_config = await agent_config.update(
            session, name="Updated Test Config", description="Updated description"
        )
        assert updated_config.name == "Updated Test Config"
        assert updated_config.description == "Updated description"

        # Delete agent configuration
        await agent_config.delete(session)

        # Verify deletion
        deleted_config = await AgentConfigModel.get_by_id(session, agent_config.id)
        assert deleted_config is None


@pytest.mark.asyncio
async def test_conversation_with_messages(database_manager):
    """Test conversation with multiple messages."""
    async for session in database_manager.get_session():
        # Create conversation
        conversation = await ConversationModel.create(
            session, user_id=uuid4(), title="Multi-message Test Conversation"
        )

        # Create multiple messages
        await MessageModel.create(
            session,
            conversation_id=conversation.id,
            role="user",
            content="First message",
        )

        await MessageModel.create(
            session,
            conversation_id=conversation.id,
            role="assistant",
            content="Second message",
        )

        await MessageModel.create(
            session,
            conversation_id=conversation.id,
            role="user",
            content="Third message",
        )

        # Get all messages for conversation
        messages = await MessageModel.get_by_conversation(session, conversation.id)
        assert len(messages) == 3

        # Messages should be ordered by creation time
        assert messages[0].content == "First message"
        assert messages[1].content == "Second message"
        assert messages[2].content == "Third message"

        # Delete conversation (should cascade delete messages)
        await conversation.delete(session)

        # Verify messages are also deleted
        conversation_messages = await MessageModel.get_by_conversation(
            session, conversation.id
        )
        assert len(conversation_messages) == 0


@pytest.mark.asyncio
async def test_database_connection_check():
    """Test database connection check functionality."""
    # Create a separate database manager for this test
    config = DatabaseConfig(database_url="sqlite+aiosqlite:///:memory:", echo_sql=False)
    db_manager = DatabaseManager(config)
    await db_manager.initialize()

    # Should be able to check connection when database is available
    is_connected = await db_manager.check_database_connection()
    assert is_connected is True

    # Close the database and check again
    await db_manager.close()
    is_connected = await db_manager.check_database_connection()
    assert is_connected is False

    # Clean up
    await db_manager.close()
