# Enhanced SimpleLangGraphClient for Consolidated Service Integration

import asyncio
import logging
from typing import Any, Dict, List

import httpx

logger = logging.getLogger(__name__)


class SimpleLangGraphClient:
    """Enhanced client for consolidated service integration"""

    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def send_message(
        self, message: str, conversation_id: str, model_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send message to consolidated workflow service"""

        payload = {
            "user_message": message,  # NEW: Correct name
            "conversation_id": conversation_id,  # This is a string from Gradio
            "workflow_mode": "workbench",  # NEW: workbench mode
            "llm_config": {
                "provider": model_config["provider"],
                "model_name": model_config["model_name"],
                "temperature": model_config["temperature"],
                "max_tokens": model_config["max_tokens"],
                "streaming": False  # Ensure streaming is set correctly
            },
            "streaming": False,  # NEW: Non-streaming
            "parameter_overrides": None,  # NEW: extensibility
            "context_data": {},  # NEW: Future context
        }

        logger.info(f"🚀 Sending request to {self.base_url}/api/v1/chat/consolidated")
        logger.debug(f"📤 Payload: {payload}")

        try:
            # NEW: Use consolidated endpoint
            response = await self.client.post(
                f"{self.base_url}/api/v1/chat/consolidated",
                json=payload,
            )

            logger.info(f"📊 Response status: {response.status_code}")
            logger.debug(f"📄 Response headers: {dict(response.headers)}")

            response.raise_for_status()
            result = await response.json()

            logger.info(f"✅ Response received successfully")
            logger.debug(f"📥 Response data: {result}")

        except httpx.TimeoutException as e:
            logger.error(f"⏱️ Request timeout: {e}")
            raise Exception(f"Request timeout after 30s: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"🔴 HTTP error {e.response.status_code}: {e.response.text}")
            raise Exception(f"API error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.error(f"💥 Unexpected error: {e}")
            raise Exception(f"Connection error: {e}")

        # NEW: Handle ConsolidatedWorkflowResponse format
        # Also support legacy format for backward compatibility
        if "assistant_response" in result:
            return_data = {
                "assistant_response": result["assistant_response"],
                "conversation_id": result["conversation_id"],
                "workflow_mode": result["workflow_mode"],
                "execution_successful": result["execution_successful"],
                "metadata": result.get("metadata", {}),
                "reply": result["assistant_response"],  # Legacy compatibility
            }
        else:
            # Legacy format support - tests expect "reply" key
            reply_content = result.get("reply", "")
            return_data = {
                "assistant_response": reply_content,
                "conversation_id": result["conversation_id"],
                "workflow_mode": "workbench",
                "execution_successful": True,
                "metadata": {},
                "reply": reply_content,  # Legacy compatibility for iteration
            }
        return return_data

    async def get_chat_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """NEW: Get history from consolidated state with legacy fallback"""
        # Try new consolidated state endpoint first
        response = await self.client.get(
            f"{self.base_url}/api/v1/conversations/{conversation_id}/state"
        )
        response.raise_for_status()
        result = await response.json()

        # Check if we got conversation_history directly
        if "conversation_history" in result:
            return result["conversation_history"]

        # Check if we got legacy messages format
        if "messages" in result:
            messages = result["messages"]
            chat_messages = []
            for msg in messages:
                if msg["role"] == "user":
                    chat_messages.append({"role": "user", "content": msg["content"]})
                elif msg["role"] == "assistant":
                    chat_messages.append(
                        {
                            "role": "assistant",
                            "content": msg.get("response", msg.get("content", "")),
                        }
                    )
            return chat_messages

        return []


# Keep LangGraphClient as an alias for backward compatibility
LangGraphClient = SimpleLangGraphClient


# Test function for the client
async def test_client():
    """Test the client functionality"""
    client = LangGraphClient()

    # Test getting chat history (will fail without server running)
    try:
        history = await client.get_chat_history("test-id")
        print(f"History: {history}")
    except Exception as e:
        print(f"Client test error (expected without server): {e}")


if __name__ == "__main__":
    asyncio.run(test_client())
