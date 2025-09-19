# Simple LangGraph Client for UI Integration

import asyncio
from typing import Any, Dict, List

import httpx


class LangGraphClient:
    """Simplified client that always queries LangGraph for state"""

    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def send_message(
        self, message: str, conversation_id: str, model_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send message to LangGraph workflow"""

        response = await self.client.post(
            f"{self.base_url}/api/v1/chat/message",
            json={
                "message": message,
                "conversation_id": conversation_id,
                "model_config": model_config,
                "workflow_mode": "workbench",
            },
        )
        response.raise_for_status()
        # The API now returns "reply" field directly
        result = await response.json()
        return result

    async def get_chat_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """Get conversation history from LangGraph (single source of truth)"""

        response = await self.client.get(
            f"{self.base_url}/api/v1/conversations/{conversation_id}/messages"
        )
        response.raise_for_status()

        result = await response.json()
        messages = result["messages"]
        # Return OpenAI-style message dictionaries for new Gradio format
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
