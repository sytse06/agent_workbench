"""Tests for retry utilities."""

import pytest

from agent_workbench.core.retry import (
    RetryExhaustedError,
    retry_api_call,
    retry_database_operation,
    retry_llm_call,
)


class TestRetryDecorators:
    """Tests for retry decorators."""

    @pytest.mark.asyncio
    async def test_retry_llm_call_success(self):
        """Test retry_llm_call decorator with successful function."""

        @retry_llm_call
        async def successful_function():
            return "success"

        result = await successful_function()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_llm_call_with_retries(self):
        """Test retry_llm_call decorator with retries."""
        from agent_workbench.core.retry import retry_with_exponential_backoff

        call_count = 0

        @retry_with_exponential_backoff(max_attempts=3, min_wait=0.1, max_wait=0.2)
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary failure")
            return "success"

        result = await flaky_function()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_llm_call_exhausted(self):
        """Test retry_llm_call decorator when retries are exhausted."""
        from agent_workbench.core.retry import retry_with_exponential_backoff

        @retry_with_exponential_backoff(max_attempts=2, min_wait=0.1, max_wait=0.2)
        async def always_failing_function():
            raise Exception("Permanent failure")

        with pytest.raises(RetryExhaustedError) as exc_info:
            await always_failing_function()

        assert "failed after 2 attempts" in str(exc_info.value)
        assert exc_info.value.attempts == 2

    def test_retry_api_call_success(self):
        """Test retry_api_call decorator with successful function."""

        @retry_api_call
        def successful_function():
            return "success"

        result = successful_function()
        assert result == "success"

    def test_retry_database_operation_success(self):
        """Test retry_database_operation decorator with successful function."""

        @retry_database_operation
        def successful_function():
            return "success"

        result = successful_function()
        assert result == "success"
