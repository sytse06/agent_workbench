"""Tests for chat models."""

from agent_workbench.models.schemas import ConversationSummary
from agent_workbench.models.api_models import (
    ChatRequest,
    ChatResponse,
    ConversationResponse,
    CreateConversationRequest,
    ModelConfig,
    ModelInfo,
    ValidationResult,
)


class TestModelConfig:
    """Tests for ModelConfig class."""

    def test_model_config_creation(self):
        """Test ModelConfig creation with default values."""
        config = ModelConfig(provider="openai", model_name="gpt-3.5-turbo")

        assert config.provider == "openai"
        assert config.model_name == "gpt-3.5-turbo"
        assert config.temperature == 0.7
        assert config.max_tokens == 1000
        assert config.top_p == 1.0
        assert config.frequency_penalty == 0.0
        assert config.system_prompt is None
        assert config.streaming is True
        assert config.extra_params == {}

    def test_model_config_with_custom_values(self):
        """Test ModelConfig creation with custom values."""
        config = ModelConfig(
            provider="ollama",
            model_name="llama3",
            temperature=0.8,
            max_tokens=2000,
            top_p=0.9,
            frequency_penalty=0.5,
            system_prompt="You are a helpful assistant.",
            streaming=False,
            extra_params={"api_key": "test-key"},
        )

        assert config.provider == "ollama"
        assert config.model_name == "llama3"
        assert config.temperature == 0.8
        assert config.max_tokens == 2000
        assert config.top_p == 0.9
        assert config.frequency_penalty == 0.5
        assert config.system_prompt == "You are a helpful assistant."
        assert config.streaming is False
        assert config.extra_params == {"api_key": "test-key"}


class TestModelInfo:
    """Tests for ModelInfo class."""

    def test_model_info_creation(self):
        """Test ModelInfo creation."""
        info = ModelInfo(
            name="gpt-4",
            display_name="GPT-4",
            context_length=8192,
            supports_streaming=True,
            supports_tools=True,
        )

        assert info.name == "gpt-4"
        assert info.display_name == "GPT-4"
        assert info.context_length == 8192
        assert info.supports_streaming is True
        assert info.supports_tools is True


class TestChatRequest:
    """Tests for ChatRequest class."""

    def test_chat_request_creation(self):
        """Test ChatRequest creation."""
        model_config = ModelConfig(provider="openai", model_name="gpt-3.5-turbo")
        request = ChatRequest(message="Hello, world!", llm_config=model_config)

        assert request.message == "Hello, world!"
        assert request.conversation_id is None
        assert request.llm_config == model_config

    def test_chat_request_with_conversation_id(self):
        """Test ChatRequest creation with conversation ID."""
        import uuid

        conv_id = uuid.uuid4()
        model_config = ModelConfig(provider="openai", model_name="gpt-3.5-turbo")
        request = ChatRequest(
            message="Hello, world!", conversation_id=conv_id, llm_config=model_config
        )

        assert request.message == "Hello, world!"
        assert request.conversation_id == conv_id
        assert request.llm_config == model_config


class TestChatResponse:
    """Tests for ChatResponse class."""

    def test_chat_response_creation(self):
        """Test ChatResponse creation."""
        import uuid

        conv_id = uuid.uuid4()
        model_config = ModelConfig(provider="openai", model_name="gpt-3.5-turbo")
        response = ChatResponse(
            message="Hello! How can I help you?",
            conversation_id=conv_id,
            model_used="openai/gpt-3.5-turbo",
            llm_config=model_config,
        )

        assert response.message == "Hello! How can I help you?"
        assert response.conversation_id == conv_id
        assert response.model_used == "openai/gpt-3.5-turbo"
        assert response.llm_config == model_config


class TestConversationSummary:
    """Tests for ConversationSummary class."""

    def test_conversation_summary_creation(self):
        """Test ConversationSummary creation."""
        import datetime
        import uuid

        conv_id = uuid.uuid4()
        now = datetime.datetime.now()

        summary = ConversationSummary(
            id=conv_id, title="Test Conversation", created_at=now, message_count=5
        )

        assert summary.id == conv_id
        assert summary.title == "Test Conversation"
        assert summary.created_at == now
        assert summary.message_count == 5
        assert summary.llm_config is None

    def test_conversation_summary_with_model_config(self):
        """Test ConversationSummary creation with model config."""
        import datetime
        import uuid

        conv_id = uuid.uuid4()
        now = datetime.datetime.now()
        model_config = ModelConfig(provider="openai", model_name="gpt-3.5-turbo")

        summary = ConversationSummary(
            id=conv_id,
            title="Test Conversation",
            created_at=now,
            message_count=5,
            llm_config=model_config,
        )

        assert summary.llm_config == model_config


class TestConversationResponse:
    """Tests for ConversationResponse class."""

    def test_conversation_response_creation(self):
        """Test ConversationResponse creation."""
        import datetime
        import uuid

        conv_id = uuid.uuid4()
        now = datetime.datetime.now()

        response = ConversationResponse(
            id=conv_id,
            title="Test Conversation",
            created_at=now,
            updated_at=now,
            messages=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ],
        )

        assert response.id == conv_id
        assert response.title == "Test Conversation"
        assert response.created_at == now
        assert response.updated_at == now
        assert len(response.messages) == 2
        assert response.llm_config is None

    def test_conversation_response_with_model_config(self):
        """Test ConversationResponse creation with model config."""
        import datetime
        import uuid

        conv_id = uuid.uuid4()
        now = datetime.datetime.now()
        model_config = ModelConfig(provider="openai", model_name="gpt-3.5-turbo")

        response = ConversationResponse(
            id=conv_id,
            title="Test Conversation",
            created_at=now,
            updated_at=now,
            messages=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ],
            llm_config=model_config,
        )

        assert response.llm_config == model_config


class TestCreateConversationRequest:
    """Tests for CreateConversationRequest class."""

    def test_create_conversation_request_creation(self):
        """Test CreateConversationRequest creation."""
        request = CreateConversationRequest(title="New Conversation")

        assert request.title == "New Conversation"
        assert request.llm_config is None

    def test_create_conversation_request_with_model_config(self):
        """Test CreateConversationRequest creation with model config."""
        model_config = ModelConfig(provider="openai", model_name="gpt-3.5-turbo")
        request = CreateConversationRequest(
            title="New Conversation", llm_config=model_config
        )

        assert request.title == "New Conversation"
        assert request.llm_config == model_config


class TestValidationResult:
    """Tests for ValidationResult class."""

    def test_validation_result_creation(self):
        """Test ValidationResult creation."""
        result = ValidationResult(is_valid=True)

        assert result.is_valid is True
        assert result.errors == []

    def test_validation_result_with_errors(self):
        """Test ValidationResult creation with errors."""
        result = ValidationResult(
            is_valid=False, errors=["Invalid provider", "Missing API key"]
        )

        assert result.is_valid is False
        assert result.errors == ["Invalid provider", "Missing API key"]
