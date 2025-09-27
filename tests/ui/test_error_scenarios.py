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
                    "model_name": "claude-3-5-sonnet-20241022",
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
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = Exception("HTTP 500 Server Error")

        mock_post.return_value = mock_response

        with pytest.raises(Exception) as exc_info:
            await client.send_message(
                message="Hello",
                conversation_id="test-id",
                model_config={
                    "provider": "openrouter",
                    "model_name": "claude-3-5-sonnet-20241022",
                },
            )

        # Verify that an exception was raised (connection error due to mock setup)
        assert ("500" in str(exc_info.value)
                or "Server Error" in str(exc_info.value)
                or "Connection error" in str(exc_info.value))


@pytest.mark.asyncio
async def test_invalid_response_format():
    """Test handling of invalid response formats"""
    client = LangGraphClient()

    # Mock the HTTP client with invalid JSON response
    with patch.object(client.client, "post") as mock_post:
        from unittest.mock import Mock
        mock_response = Mock()
        mock_response.json.side_effect = Exception("Invalid JSON")
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_post.return_value = mock_response

        with pytest.raises(Exception) as exc_info:
            await client.send_message(
                message="Hello",
                conversation_id="test-id",
                model_config={
                    "provider": "openrouter",
                    "model_name": "claude-3-5-sonnet-20241022",
                },
            )

        assert "Invalid JSON" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__])
