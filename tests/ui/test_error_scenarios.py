# Error scenario tests

from unittest.mock import AsyncMock, patch

import pytest

from agent_workbench.ui.components.simple_client import LangGraphClient


@pytest.mark.asyncio
async def test_network_error_handling():
    """Test handling of network errors"""
    client = LangGraphClient()

    # Mock the HTTP client to raise a network error
    with patch.object(client.client, "post") as mock_post:
        mock_post.side_effect = Exception("Network timeout")

        with pytest.raises(Exception) as exc_info:
            await client.send_message(
                message="Hello",
                conversation_id="test-id",
                model_config={
                    "provider": "openrouter",
                    "model": "claude-3-5-sonnet-20241022",
                },
            )

        assert "Network timeout" in str(exc_info.value)


@pytest.mark.asyncio
async def test_http_error_handling():
    """Test handling of HTTP errors"""
    client = LangGraphClient()

    # Mock the HTTP client to return an error status
    with patch.object(client.client, "post") as mock_post:
        # Create a mock response that raises on status check
        from unittest.mock import Mock

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception(
            "HTTP 500 Internal Server Error"
        )

        # Set up the async mock correctly
        async def mock_post_coroutine(*args, **kwargs):
            return mock_response

        mock_post.side_effect = mock_post_coroutine

        with pytest.raises(Exception) as exc_info:
            await client.send_message(
                message="Hello",
                conversation_id="test-id",
                model_config={
                    "provider": "openrouter",
                    "model": "claude-3-5-sonnet-20241022",
                },
            )

        assert "HTTP 500 Internal Server Error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_invalid_response_format():
    """Test handling of invalid response formats"""
    client = LangGraphClient()

    # Mock the HTTP client with invalid JSON response
    with patch.object(client.client, "post") as mock_post:
        mock_post.return_value.json.side_effect = Exception("Invalid JSON")
        mock_post.return_value.raise_for_status = AsyncMock()

        with pytest.raises(Exception) as exc_info:
            await client.send_message(
                message="Hello",
                conversation_id="test-id",
                model_config={
                    "provider": "openrouter",
                    "model": "claude-3-5-sonnet-20241022",
                },
            )

        assert "Invalid JSON" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__])
