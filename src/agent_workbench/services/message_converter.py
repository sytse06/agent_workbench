"""Message format conversion between LangChain and standard formats."""

from typing import List

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)

from ..models.standard_messages import StandardMessage


class MessageConverter:
    """Converter between LangChain and standard message formats."""

    @staticmethod
    def to_langchain_messages(messages: List[StandardMessage]) -> List[BaseMessage]:
        """
        Convert standard messages to LangChain format.

        Args:
            messages: List of standard messages

        Returns:
            List of LangChain messages
        """
        langchain_messages = []
        for msg in messages:
            if msg.role == "user":
                langchain_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                langchain_messages.append(AIMessage(content=msg.content))
            elif msg.role == "system":
                langchain_messages.append(SystemMessage(content=msg.content))
            # Note: tool messages would be handled here if needed
        return langchain_messages

    @staticmethod
    def from_langchain_message(message: BaseMessage) -> StandardMessage:
        """
        Convert LangChain message to standard format.

        Args:
            message: LangChain message

        Returns:
            Standard message
        """
        role = "user"
        if isinstance(message, HumanMessage):
            role = "user"
        elif isinstance(message, AIMessage):
            role = "assistant"
        elif isinstance(message, SystemMessage):
            role = "system"

        timestamp = None
        if hasattr(message, "additional_kwargs"):
            timestamp = message.additional_kwargs.get("timestamp")

        return StandardMessage(
            role=role, content=str(message.content), timestamp=timestamp
        )

    @staticmethod
    def to_standard_messages(messages: List[BaseMessage]) -> List[StandardMessage]:
        """
        Convert LangChain messages to standard format.

        Args:
            messages: List of LangChain messages

        Returns:
            List of standard messages
        """
        return [MessageConverter.from_langchain_message(msg) for msg in messages]
