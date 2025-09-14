"""Retry utilities for LLM service with exponential backoff."""

import asyncio
import logging
from functools import wraps
from typing import Callable, Optional, Type, TypeVar

from tenacity import (
    after_log,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .exceptions import RetryExhaustedError

# Set up logging
logger = logging.getLogger(__name__)

T = TypeVar("T")

# Default retry configuration
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_MIN_WAIT = 1
DEFAULT_MAX_WAIT = 10
DEFAULT_EXPONENTIAL_BASE = 2


def create_retry_decorator(
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    min_wait: float = DEFAULT_MIN_WAIT,
    max_wait: float = DEFAULT_MAX_WAIT,
    exponential_base: float = DEFAULT_EXPONENTIAL_BASE,
    retry_exceptions: tuple[Type[Exception], ...] = (Exception,),
    logger: Optional[logging.Logger] = None,
):
    """
    Create a retry decorator with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries (seconds)
        max_wait: Maximum wait time between retries (seconds)
        exponential_base: Base for exponential backoff calculation
        retry_exceptions: Tuple of exception types to retry on
        logger: Logger instance for retry messages

    Returns:
        retry decorator function
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(
            multiplier=1, min=min_wait, max=max_wait, exp_base=exponential_base
        ),
        retry=retry_if_exception_type(retry_exceptions),
        before_sleep=before_sleep_log(
            logger or logging.getLogger(__name__), logging.WARNING
        ),
        after=after_log(logger or logging.getLogger(__name__), logging.ERROR),
        reraise=True,
    )


def retry_with_exponential_backoff(
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    min_wait: float = DEFAULT_MIN_WAIT,
    max_wait: float = DEFAULT_MAX_WAIT,
    exponential_base: float = DEFAULT_EXPONENTIAL_BASE,
    retry_exceptions: tuple[Type[Exception], ...] = (Exception,),
    logger: Optional[logging.Logger] = None,
):
    """
    Decorator for retrying async functions with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries (seconds)
        max_wait: Maximum wait time between retries (seconds)
        exponential_base: Base for exponential backoff calculation
        retry_exceptions: Tuple of exception types to retry on
        logger: Logger instance for retry messages

    Returns:
        Decorator function
    """
    retry_decorator = create_retry_decorator(
        max_attempts=max_attempts,
        min_wait=min_wait,
        max_wait=max_wait,
        exponential_base=exponential_base,
        retry_exceptions=retry_exceptions,
        logger=logger,
    )

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            try:
                # Apply tenacity retry decorator
                retrying_func = retry_decorator(func)
                result = await retrying_func(*args, **kwargs)
                return result  # type: ignore
            except Exception as e:
                # If all retries exhausted, raise our custom exception
                raise RetryExhaustedError(
                    f"Function {func.__name__} failed after {max_attempts} "
                    f"attempts: {str(e)}",
                    attempts=max_attempts,
                ) from e

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            try:
                # Apply tenacity retry decorator
                retrying_func = retry_decorator(func)
                result = retrying_func(*args, **kwargs)
                return result  # type: ignore
            except Exception as e:
                # If all retries exhausted, raise our custom exception
                raise RetryExhaustedError(
                    f"Function {func.__name__} failed after {max_attempts} "
                    f"attempts: {str(e)}",
                    attempts=max_attempts,
                ) from e

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


# Pre-configured retry decorators for common use cases

retry_llm_call = retry_with_exponential_backoff(
    max_attempts=3,
    min_wait=1,
    max_wait=10,
    retry_exceptions=(Exception,),
    logger=logger,
)

retry_api_call = retry_with_exponential_backoff(
    max_attempts=5,
    min_wait=2,
    max_wait=30,
    retry_exceptions=(Exception,),
    logger=logger,
)

retry_database_operation = retry_with_exponential_backoff(
    max_attempts=3,
    min_wait=0.5,
    max_wait=5,
    retry_exceptions=(Exception,),
    logger=logger,
)
