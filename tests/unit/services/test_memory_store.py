"""Unit tests for memory_store module."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from agent_workbench.services.memory_store import read_memory


@pytest.mark.asyncio
async def test_read_memory_returns_content_when_found():
    store = AsyncMock()
    item = MagicMock()
    item.value = {"content": "be concise"}
    store.aget.return_value = item

    result = await read_memory(store, "sess-123", "agents")

    assert result == "be concise"
    store.aget.assert_called_once_with(("sess-123", "memories"), "agents")


@pytest.mark.asyncio
async def test_read_memory_returns_empty_when_not_found():
    store = AsyncMock()
    store.aget.return_value = None

    result = await read_memory(store, "sess-123", "agents")

    assert result == ""


@pytest.mark.asyncio
async def test_read_memory_returns_empty_on_exception():
    store = AsyncMock()
    store.aget.side_effect = Exception("store error")

    result = await read_memory(store, "sess-123", "agents")

    assert result == ""


@pytest.mark.asyncio
async def test_read_memory_returns_empty_when_value_is_none():
    store = AsyncMock()
    item = MagicMock()
    item.value = None
    store.aget.return_value = item

    result = await read_memory(store, "sess-123", "domain_context")

    assert result == ""


@pytest.mark.asyncio
async def test_read_memory_returns_empty_when_content_key_missing():
    store = AsyncMock()
    item = MagicMock()
    item.value = {"other_key": "something"}
    store.aget.return_value = item

    result = await read_memory(store, "sess-123", "agents")

    assert result == ""
