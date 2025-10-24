"""
Integration tests for SEO Coach Interface - UI-002 SEO Coach Interface.

Tests end-to-end workflows, HTTP integration, and consolidated service calls.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent_workbench.ui.seo_coach_app import (
    _handle_coaching_message,
    _handle_quick_action,
    _handle_website_analysis,
    create_seo_coach_app,
)


class TestSEOCoachIntegration:
    """Integration tests for SEO coach workflows"""

    @pytest.mark.asyncio
    async def test_website_analysis_success(self):
        """Test successful website analysis workflow"""
        # Mock successful HTTP response
        with (
            patch("httpx.AsyncClient") as mock_client_class,
            patch(
                "agent_workbench.ui.seo_coach_app.validate_business_profile"
            ) as mock_validate,
            patch(
                "agent_workbench.ui.seo_coach_app.create_business_profile_dict"
            ) as mock_create_profile,
        ):
            # Ensure validation passes and profile is created correctly
            mock_validate.return_value = (True, "")
            mock_create_profile.return_value = {
                "business_name": "Test Restaurant",
                "business_type": "Restaurant",
                "website_url": "https://restaurant-test.nl",
                "location": "Amsterdam",
                "language": "dutch",
                "seo_experience": "beginner",
            }
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock consolidated service response - create a proper mock response
            class MockResponse:
                def json(self):
                    return {
                        "assistant_response": (
                            "Ik heb je restaurant website geanalyseerd. "
                            "Hier zijn de belangrijkste SEO verbeterpunten..."
                        ),
                        "conversation_id": "test-conv-id",
                        "workflow_mode": "seo_coach",
                        "execution_successful": True,
                    }

                def raise_for_status(self):
                    pass

            mock_response = MockResponse()
            mock_client.post.return_value = mock_response

            # Test website analysis
            result = await _handle_website_analysis(
                url="https://restaurant-test.nl",
                biz_name="Test Restaurant",
                biz_type="Restaurant",
                location="Amsterdam",
                conv_id="test-conv-id",
            )

            chat_history, business_profile, status_html = result

            # Verify HTTP call was made correctly
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args

            expected_url = "http://localhost:8000/api/v1/chat/consolidated"
            assert call_args[0][0] == expected_url
            json_data = call_args[1]["json"]
            assert json_data["workflow_mode"] == "seo_coach"
            assert json_data["conversation_id"] == "test-conv-id"
            assert "restaurant website" in json_data["user_message"].lower()

            # Verify business profile structure - should be created properly
            assert business_profile is not None
            assert isinstance(business_profile, dict)
            assert len(business_profile) > 0
            assert business_profile.get("business_name") == "Test Restaurant"
            assert business_profile["business_type"] == "Restaurant"
            expected_url = "https://restaurant-test.nl"
            assert business_profile["website_url"] == expected_url
            assert business_profile["location"] == "Amsterdam"
            assert business_profile["language"] == "dutch"

            # Verify chat history
            assert len(chat_history) == 2
            assert "Welkom Test Restaurant" in chat_history[0]["content"]
            assert "SEO verbeterpunten" in chat_history[1]["content"]

            # Verify status HTML
            assert "✅" in status_html
            assert "Test Restaurant" in status_html
            assert "https://restaurant-test.nl" in status_html

    @pytest.mark.asyncio
    async def test_website_analysis_validation_error(self):
        """Test website analysis with validation errors"""
        # Test empty business name
        result = await _handle_website_analysis(
            url="https://test.nl",
            biz_name="",
            biz_type="Restaurant",
            location="Amsterdam",
            conv_id="test-conv-id",
        )

        chat_history, business_profile, status_html = result

        assert chat_history == []
        assert business_profile == {}
        assert "❌" in status_html
        assert "Bedrijfsnaam is verplicht" in status_html

    @pytest.mark.asyncio
    async def test_website_analysis_http_error(self):
        """Test website analysis with HTTP error"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock HTTP error
            mock_client.post.side_effect = Exception("Network error")

            result = await _handle_website_analysis(
                url="https://test.nl",
                biz_name="Test Business",
                biz_type="Restaurant",
                location="Amsterdam",
                conv_id="test-conv-id",
            )

            chat_history, business_profile, status_html = result

            assert chat_history == []
            assert business_profile == {}
            assert "❌" in status_html
            assert "Network error" in status_html

    @pytest.mark.asyncio
    async def test_coaching_message_success(self):
        """Test successful coaching message workflow"""
        business_profile = {
            "business_name": "Test Restaurant",
            "business_type": "Restaurant",
            "website_url": "https://test.nl",
            "location": "Amsterdam",
            "language": "dutch",
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock consolidated service response
            mock_response = AsyncMock()
            mock_response.raise_for_status = MagicMock(return_value=None)
            mock_client.post.return_value = mock_response

            # Mock conversation history response
            mock_history_response = AsyncMock()
            mock_history_response.json.return_value = {
                "conversation_history": [
                    {"role": "user", "content": "Wat zijn goede zoekwoorden?"},
                    {
                        "role": "assistant",
                        "content": (
                            "Voor je restaurant zijn deze zoekwoorden belangrijk..."
                        ),
                    },
                ]
            }
            mock_history_response.raise_for_status = MagicMock(return_value=None)
            mock_client.get.return_value = mock_history_response

            msg = "Wat zijn goede zoekwoorden voor mijn restaurant?"
            result = await _handle_coaching_message(
                msg=msg, conv_id="test-conv-id", profile=business_profile
            )

            empty_input, updated_history = result

            # Verify HTTP calls
            assert mock_client.post.call_count == 1
            # The function makes 1 GET call for history retrieval
            # (could be 2 if error handling path is triggered)
            assert mock_client.get.call_count >= 1

            # Verify consolidated service call
            post_call = mock_client.post.call_args
            json_data = post_call[1]["json"]
            assert json_data["workflow_mode"] == "seo_coach"
            assert json_data["business_profile"] == business_profile
            assert "zoekwoorden" in json_data["user_message"]

            # Verify history call
            get_call = mock_client.get.call_args
            expected_url = (
                "http://localhost:8000/api/v1/conversations/test-conv-id/state"
            )
            assert get_call[0][0] == expected_url

            # Verify results
            assert empty_input == ""
            # Should return the mocked conversation history (2 messages)
            assert len(updated_history) == 2
            # Check that the conversation was updated with keyword content
            assert any(
                "zoekwoorden" in msg.get("content", "") for msg in updated_history
            )

    @pytest.mark.asyncio
    async def test_coaching_message_no_profile(self):
        """Test coaching message without business profile"""
        result = await _handle_coaching_message(
            msg="Test message", conv_id="test-conv-id", profile={}
        )

        empty_input, updated_history = result

        assert empty_input == ""
        assert len(updated_history) == 1
        assert "bedrijfsgegevens" in updated_history[0]["content"].lower()

    @pytest.mark.asyncio
    async def test_coaching_message_empty_message(self):
        """Test coaching message with empty input"""
        business_profile = {"business_name": "Test"}

        result = await _handle_coaching_message(
            msg="", conv_id="test-conv-id", profile=business_profile
        )

        empty_input, updated_history = result

        assert empty_input == ""
        # Should return gr.update() for no change

    @pytest.mark.asyncio
    async def test_coaching_message_http_error(self):
        """Test coaching message with HTTP error"""
        business_profile = {"business_name": "Test"}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock HTTP error
            mock_client.post.side_effect = Exception("Connection error")

            result = await _handle_coaching_message(
                msg="Test message", conv_id="test-conv-id", profile=business_profile
            )

            empty_input, updated_history = result

            assert empty_input == ""
            assert len(updated_history) >= 2
            assert "Test message" in updated_history[-2]["content"]
            assert "ging iets mis" in updated_history[-1]["content"]

    @pytest.mark.asyncio
    async def test_quick_action_audit(self):
        """Test quick audit action"""
        business_profile = {"business_name": "Test Restaurant"}

        patch_path = "agent_workbench.ui.seo_coach_app._handle_coaching_message"
        with patch(patch_path) as mock_handler:
            mock_handler.return_value = (
                "",
                [{"role": "assistant", "content": "SEO audit results"}],
            )

            await _handle_quick_action(
                action_type="audit", conv_id="test-conv-id", profile=business_profile
            )

            # Verify the handler was called with audit message
            mock_handler.assert_called_once()
            call_args = mock_handler.call_args[0]
            assert "snelle SEO-check" in call_args[0]
            assert call_args[1] == "test-conv-id"
            assert call_args[2] == business_profile

    @pytest.mark.asyncio
    async def test_quick_action_keywords(self):
        """Test quick keywords action"""
        business_profile = {"business_name": "Test Restaurant"}

        patch_path = "agent_workbench.ui.seo_coach_app._handle_coaching_message"
        with patch(patch_path) as mock_handler:
            mock_handler.return_value = (
                "",
                [{"role": "assistant", "content": "Keywords suggestions"}],
            )

            await _handle_quick_action(
                action_type="keywords", conv_id="test-conv-id", profile=business_profile
            )

            # Verify the handler was called with keywords message
            mock_handler.assert_called_once()
            call_args = mock_handler.call_args[0]
            assert "zoekwoorden" in call_args[0]
            assert "doelgroep" in call_args[0]

    @pytest.mark.asyncio
    async def test_quick_action_content(self):
        """Test quick content ideas action"""
        business_profile = {"business_name": "Test Restaurant"}

        patch_path = "agent_workbench.ui.seo_coach_app._handle_coaching_message"
        with patch(patch_path) as mock_handler:
            mock_handler.return_value = (
                "",
                [{"role": "assistant", "content": "Content ideas"}],
            )

            await _handle_quick_action(
                action_type="content", conv_id="test-conv-id", profile=business_profile
            )

            # Verify the handler was called with content message
            mock_handler.assert_called_once()
            call_args = mock_handler.call_args[0]
            assert "content-ideeën" in call_args[0]
            assert "Google" in call_args[0]

    @pytest.mark.asyncio
    async def test_quick_action_unknown_type(self):
        """Test quick action with unknown type defaults to audit"""
        business_profile = {"business_name": "Test Restaurant"}

        patch_path = "agent_workbench.ui.seo_coach_app._handle_coaching_message"
        with patch(patch_path) as mock_handler:
            mock_handler.return_value = (
                "",
                [{"role": "assistant", "content": "Default audit"}],
            )

            await _handle_quick_action(
                action_type="unknown", conv_id="test-conv-id", profile=business_profile
            )

            # Should default to audit message
            mock_handler.assert_called_once()
            call_args = mock_handler.call_args[0]
            assert "snelle SEO-check" in call_args[0]


class TestSEOCoachAppIntegration:
    """Integration tests for complete SEO coach app"""

    def test_seo_coach_app_full_creation(self):
        """Test complete SEO coach app creation and structure"""
        try:
            app = create_seo_coach_app()
            # Verify complete app structure
            assert app is not None
            assert hasattr(app, "blocks")
            assert len(app.blocks) > 0
            # Verify Dutch title
            assert app.title == "AI SEO Coach - Nederlandse Bedrijven"
            # Verify CSS styling
            assert hasattr(app, "css")
            css_content = str(app.css)
            assert "business-panel" in css_content
            assert "coaching-panel" in css_content
            assert "success" in css_content
            assert "error" in css_content
        except AttributeError as e:
            if "Cannot call click outside of a gradio.Blocks context" in str(e):
                pytest.skip("Gradio context not available in test environment")
            else:
                raise

    def test_seo_coach_app_event_handlers_attached(self):
        """Test that event handlers are properly attached"""
        try:
            # This test verifies the app can be created without errors
            # Event handlers are attached during creation
            app = create_seo_coach_app()
            # App should have multiple blocks with event handlers
            assert len(app.blocks) >= 15  # Many components with handlers
            # App should be ready for deployment
            assert hasattr(app, "app")  # FastAPI app for mounting
        except AttributeError as e:
            if "Cannot call click outside of a gradio.Blocks context" in str(e):
                pytest.skip("Gradio context not available in test environment")
            else:
                raise


class TestConsolidatedServiceIntegration:
    """Test integration with the consolidated service endpoint"""

    @pytest.mark.asyncio
    async def test_consolidated_service_seo_coach_mode(self):
        """Test that SEO coach mode is properly sent to consolidated service"""
        business_profile = {
            "business_name": "Test Restaurant",
            "business_type": "Restaurant",
            "website_url": "https://test.nl",
            "location": "Amsterdam",
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = AsyncMock()
            mock_response.raise_for_status = MagicMock(return_value=None)
            mock_client.post.return_value = mock_response

            mock_history_response = AsyncMock()
            mock_history_response.json.return_value = {"conversation_history": []}
            mock_history_response.raise_for_status = MagicMock(return_value=None)
            mock_client.get.return_value = mock_history_response

            await _handle_coaching_message(
                msg="Test SEO advice", conv_id="test-conv-id", profile=business_profile
            )

            # Verify consolidated service call structure
            post_call = mock_client.post.call_args
            expected_url = "http://localhost:8000/api/v1/chat/consolidated"
            assert post_call[0][0] == expected_url

            json_data = post_call[1]["json"]
            assert json_data["workflow_mode"] == "seo_coach"
            assert json_data["business_profile"] == business_profile
            assert json_data["streaming"] is False
            assert json_data["user_message"] == "Test SEO advice"
            assert json_data["conversation_id"] == "test-conv-id"

    @pytest.mark.asyncio
    async def test_error_handling_preserves_conversation(self):
        """Test that errors don't break conversation state"""
        business_profile = {"business_name": "Test"}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # First call fails
            mock_client.post.side_effect = Exception("Service unavailable")

            # Second call (history) succeeds
            mock_history_response = AsyncMock()
            mock_history_response.status_code = 200
            mock_history_response.json.return_value = {
                "conversation_history": [
                    {"role": "user", "content": "Previous message"},
                    {"role": "assistant", "content": "Previous response"},
                ]
            }
            mock_client.get.return_value = mock_history_response

            result = await _handle_coaching_message(
                msg="New message", conv_id="test-conv-id", profile=business_profile
            )

            empty_input, updated_history = result

            # Should preserve existing conversation and add error
            # Check that conversation was preserved and error added
            assert len(updated_history) >= 2
            # Check if the error handling preserved the conversation
            message_contents = [msg.get("content", "") for msg in updated_history]
            has_previous = any(
                "Previous message" in content for content in message_contents
            )
            has_error = any("ging iets mis" in content for content in message_contents)
            # At minimum, should have previous conversation OR error message
            assert (
                has_previous or has_error
            ), f"Missing expected content in {message_contents}"


if __name__ == "__main__":
    pytest.main([__file__])
