# PROD-001: Production Hardening

## Status

**Status**: Ready for Implementation
**Date**: January 15, 2025
**Decision Makers**: Human Architect
**Task ID**: PROD-001-production-hardening
**Phase**: 2.8 (Final Phase)
**Dependencies**: TOOL-002 (LangChain-MCP Integration)

## Context

Phase 2.8 represents the **FINAL phase before v0.2.0 release**. All previous phases (2.1-2.7) must be complete before starting this phase. This phase focuses on production readiness: comprehensive error handling, resource management, performance optimization, monitoring, and observability.

The system at this point has:
- ✅ Authentication and user management (Phase 2.1)
- ✅ Context retrieval with embeddings (Phase 2.2)
- ✅ Agent executor with working memory (Phase 2.3)
- ✅ Middleware pipeline with PII redaction (Phase 2.4)
- ✅ Conversation summarization (Phase 2.5)
- ✅ MCP server integration (Phase 2.6)
- ✅ LangChain-MCP bridge with tool adapters (Phase 2.7)

**This phase adds the FINAL layer**: production hardening to ensure stability, reliability, and operability at scale.

## Architecture Scope

### What's Included:

**1. Health Checks & Monitoring**
- Comprehensive health endpoint with service status checks
- Agent service health (model connectivity, working memory)
- MCP server health (connection status, tool availability)
- Database health (connection pool, query performance)
- Middleware health (pipeline integrity)
- Resource usage metrics (memory, CPU, disk)

**2. Error Boundaries & Recovery**
- Global error handlers for FastAPI routes
- LangGraph error boundaries with graceful degradation
- Middleware error isolation (one middleware failure doesn't crash pipeline)
- Tool call error recovery (retry with exponential backoff)
- Database transaction rollback on errors
- Comprehensive error logging with stack traces

**3. Rate Limiting & Resource Management**
- Per-user rate limiting for agent calls
- Token bucket algorithm for request throttling
- Concurrent request limits per user/session
- Database connection pool management
- MCP connection pool with max connections
- Temp file cleanup (automatic garbage collection)
- Working memory cleanup (expired tasks)

**4. Performance Optimization**
- Request/response validation caching
- Database query optimization (prepared statements, indexes)
- Middleware performance tracking
- Tool call performance metrics
- LangGraph state serialization optimization
- Async operation profiling

**5. Production Logging & Observability**
- Structured logging with correlation IDs
- Request tracing through entire pipeline
- Performance metrics (p50, p95, p99 latencies)
- Error aggregation and alerting hooks
- Audit logging for sensitive operations
- Debug mode with detailed execution traces

**6. Concurrency & Thread Safety**
- Thread-safe database connection management
- Async operation coordination
- Working memory concurrent access protection
- MCP connection pooling with semaphores
- File system operation locking

### What's Explicitly Excluded:

- Frontend performance optimization (Phase 3)
- Advanced caching strategies (Redis, Memcached)
- Distributed tracing (OpenTelemetry, Jaeger)
- External monitoring services (Prometheus, Grafana)
- Load balancing and horizontal scaling
- CDN integration
- Advanced security hardening (WAF, DDoS protection)
- Kubernetes deployment configurations

## Architectural Decisions

### 1. Health Check System

**Comprehensive Service Health Monitoring**:

```python
# api/routes/health.py

from fastapi import APIRouter, Depends
from typing import Dict, Any, List
from datetime import datetime
from pydantic import BaseModel
import psutil
import asyncio

class ServiceStatus(BaseModel):
    """Status for individual service."""
    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    latency_ms: Optional[int]
    message: Optional[str]
    timestamp: datetime

class HealthResponse(BaseModel):
    """Overall system health."""
    status: str  # "healthy", "degraded", "unhealthy"
    version: str
    timestamp: datetime
    services: List[ServiceStatus]
    resources: Dict[str, Any]

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Comprehensive health check endpoint.

    Checks:
    - Database connectivity
    - Agent service (model connectivity)
    - MCP servers (tool availability)
    - Middleware pipeline
    - Resource usage (memory, CPU, disk)
    """
    services = await asyncio.gather(
        check_database_health(),
        check_agent_health(),
        check_mcp_health(),
        check_middleware_health(),
        return_exceptions=True
    )

    # Aggregate status
    all_healthy = all(s.status == "healthy" for s in services if isinstance(s, ServiceStatus))
    any_degraded = any(s.status == "degraded" for s in services if isinstance(s, ServiceStatus))

    overall_status = "healthy"
    if not all_healthy:
        overall_status = "degraded" if any_degraded else "unhealthy"

    return HealthResponse(
        status=overall_status,
        version=get_app_version(),
        timestamp=datetime.utcnow(),
        services=services,
        resources=get_resource_usage()
    )

async def check_database_health() -> ServiceStatus:
    """Check database connectivity and performance."""
    start = time.time()
    try:
        db = get_database()
        # Simple query to test connection
        await db.execute_query("SELECT 1")

        latency = int((time.time() - start) * 1000)

        return ServiceStatus(
            name="database",
            status="healthy" if latency < 100 else "degraded",
            latency_ms=latency,
            message=f"Query latency: {latency}ms",
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return ServiceStatus(
            name="database",
            status="unhealthy",
            latency_ms=None,
            message=f"Connection failed: {str(e)}",
            timestamp=datetime.utcnow()
        )

async def check_agent_health() -> ServiceStatus:
    """Check agent service health."""
    start = time.time()
    try:
        agent_service = get_agent_service()

        # Test model connectivity (lightweight call)
        test_response = await agent_service.health_check()

        latency = int((time.time() - start) * 1000)

        return ServiceStatus(
            name="agent_service",
            status="healthy" if test_response.success else "degraded",
            latency_ms=latency,
            message=test_response.message,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return ServiceStatus(
            name="agent_service",
            status="unhealthy",
            latency_ms=None,
            message=f"Health check failed: {str(e)}",
            timestamp=datetime.utcnow()
        )

async def check_mcp_health() -> ServiceStatus:
    """Check MCP server connectivity."""
    start = time.time()
    try:
        mcp_manager = get_mcp_manager()

        # Check all registered servers
        server_statuses = await mcp_manager.check_all_servers()

        all_healthy = all(s["status"] == "connected" for s in server_statuses)

        latency = int((time.time() - start) * 1000)

        return ServiceStatus(
            name="mcp_servers",
            status="healthy" if all_healthy else "degraded",
            latency_ms=latency,
            message=f"{len([s for s in server_statuses if s['status'] == 'connected'])}/{len(server_statuses)} servers connected",
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return ServiceStatus(
            name="mcp_servers",
            status="unhealthy",
            latency_ms=None,
            message=f"MCP check failed: {str(e)}",
            timestamp=datetime.utcnow()
        )

def get_resource_usage() -> Dict[str, Any]:
    """Get system resource usage."""
    return {
        "memory_percent": psutil.virtual_memory().percent,
        "memory_available_mb": psutil.virtual_memory().available / (1024 * 1024),
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "disk_usage_percent": psutil.disk_usage("/").percent,
        "process_count": len(psutil.pids())
    }
```

### 2. Error Boundaries & Recovery

**Comprehensive Error Handling Strategy**:

```python
# middleware/error_boundary.py

from langchain.agents.middleware import BaseMiddleware
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
import traceback

logger = logging.getLogger(__name__)

class ErrorBoundaryMiddleware(BaseMiddleware):
    """
    Error boundary for agent execution.

    Provides:
    - Graceful error handling
    - Automatic retry with exponential backoff
    - Error logging with context
    - Fallback responses
    """

    def __init__(self, max_retries: int = 3, fallback_enabled: bool = True):
        self.max_retries = max_retries
        self.fallback_enabled = fallback_enabled
        self._retry_count = 0

    async def before_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize error tracking."""
        state["error_boundary"] = {
            "retry_count": 0,
            "errors": [],
            "recovery_attempts": []
        }
        return state

    async def on_error(self, error: Exception, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle errors with recovery strategy.

        Strategy:
        1. Log error with full context
        2. Attempt retry if retryable error
        3. Use fallback response if max retries exceeded
        4. Update state with error information
        """
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "stack_trace": traceback.format_exc(),
            "timestamp": datetime.utcnow().isoformat()
        }

        state["error_boundary"]["errors"].append(error_info)

        # Check if error is retryable
        if self._is_retryable_error(error):
            self._retry_count += 1
            state["error_boundary"]["retry_count"] = self._retry_count

            if self._retry_count <= self.max_retries:
                logger.warning(
                    f"Retryable error occurred (attempt {self._retry_count}/{self.max_retries}): {error}",
                    extra={"state": state}
                )

                # Exponential backoff
                await asyncio.sleep(2 ** self._retry_count)

                state["error_boundary"]["recovery_attempts"].append({
                    "attempt": self._retry_count,
                    "action": "retry"
                })

                # Return state to retry
                return state

        # Max retries exceeded or non-retryable error
        logger.error(
            f"Agent execution failed: {error}",
            extra={
                "error_type": type(error).__name__,
                "state": state,
                "stack_trace": traceback.format_exc()
            }
        )

        # Use fallback response if enabled
        if self.fallback_enabled:
            state["agent_response"] = self._get_fallback_response(error, state)
            state["execution_successful"] = False
            state["error_message"] = str(error)
        else:
            # Re-raise if no fallback
            raise

        return state

    def _is_retryable_error(self, error: Exception) -> bool:
        """Check if error should trigger retry."""
        retryable_types = (
            # Network errors
            TimeoutError,
            ConnectionError,
            # API errors
            httpx.ReadTimeout,
            httpx.ConnectTimeout,
            # Model errors
            openai.RateLimitError,
            anthropic.RateLimitError,
        )

        return isinstance(error, retryable_types)

    def _get_fallback_response(self, error: Exception, state: Dict[str, Any]) -> str:
        """Generate fallback response for user."""
        error_type = type(error).__name__

        fallback_messages = {
            "TimeoutError": "I apologize, but my response took too long to generate. Please try again.",
            "RateLimitError": "I'm currently experiencing high demand. Please wait a moment and try again.",
            "ConnectionError": "I'm having trouble connecting to my services. Please try again shortly.",
        }

        return fallback_messages.get(
            error_type,
            "I encountered an unexpected issue. Please try rephrasing your request."
        )


# api/middleware/global_error_handler.py

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger(__name__)

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for FastAPI.

    Catches all unhandled exceptions and returns structured error response.
    """
    # Log error with request context
    logger.error(
        f"Unhandled exception: {exc}",
        extra={
            "url": str(request.url),
            "method": request.method,
            "client": request.client.host if request.client else None,
            "stack_trace": traceback.format_exc()
        }
    )

    # Determine status code
    if isinstance(exc, RequestValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        detail = "Request validation failed"
    elif isinstance(exc, ValueError):
        status_code = status.HTTP_400_BAD_REQUEST
        detail = str(exc)
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        detail = "Internal server error"

    return JSONResponse(
        status_code=status_code,
        content={
            "error": type(exc).__name__,
            "detail": detail,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Register in main.py
from fastapi import FastAPI
from api.middleware.global_error_handler import global_exception_handler

app = FastAPI()
app.add_exception_handler(Exception, global_exception_handler)
```

### 3. Rate Limiting & Resource Management

**Token Bucket Rate Limiting**:

```python
# middleware/rate_limiter.py

from fastapi import Request, HTTPException, status
from typing import Dict, Optional
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict

class TokenBucket:
    """
    Token bucket rate limiter.

    Algorithm:
    - Bucket has capacity for N tokens
    - Tokens refill at rate R per second
    - Request consumes 1 token
    - Request blocked if no tokens available
    """

    def __init__(self, capacity: int, refill_rate: float):
        """
        Args:
            capacity: Max tokens in bucket
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = datetime.utcnow()
        self._lock = asyncio.Lock()

    async def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens.

        Returns:
            True if tokens consumed, False if rate limited
        """
        async with self._lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            return False

    def _refill(self) -> None:
        """Refill tokens based on time elapsed."""
        now = datetime.utcnow()
        elapsed = (now - self.last_refill).total_seconds()

        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now


class RateLimiter:
    """
    Per-user rate limiter using token bucket algorithm.

    Limits:
    - Agent calls: 60 per minute
    - Concurrent requests: 5 per user
    """

    def __init__(self):
        # user_id -> TokenBucket
        self._buckets: Dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(capacity=60, refill_rate=1.0)  # 60 tokens, 1/sec refill
        )

        # user_id -> active request count
        self._concurrent_requests: Dict[str, int] = defaultdict(int)
        self._concurrent_limit = 5
        self._lock = asyncio.Lock()

    async def check_rate_limit(self, user_id: str) -> None:
        """
        Check if user is within rate limits.

        Raises:
            HTTPException: If rate limit exceeded
        """
        # Check token bucket
        bucket = self._buckets[user_id]
        if not await bucket.consume():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": "60"}
            )

        # Check concurrent requests
        async with self._lock:
            if self._concurrent_requests[user_id] >= self._concurrent_limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many concurrent requests (max {self._concurrent_limit})"
                )

            self._concurrent_requests[user_id] += 1

    async def release(self, user_id: str) -> None:
        """Release concurrent request slot."""
        async with self._lock:
            self._concurrent_requests[user_id] = max(0, self._concurrent_requests[user_id] - 1)


# Middleware integration
rate_limiter = RateLimiter()

async def rate_limit_middleware(request: Request, call_next):
    """FastAPI middleware for rate limiting."""
    # Extract user_id from JWT token
    user_id = await get_current_user_id(request)

    if user_id:
        await rate_limiter.check_rate_limit(user_id)

        try:
            response = await call_next(request)
            return response
        finally:
            await rate_limiter.release(user_id)
    else:
        # No user_id, skip rate limiting
        return await call_next(request)
```

**Resource Cleanup**:

```python
# services/cleanup_service.py

import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List
import asyncio
import logging

logger = logging.getLogger(__name__)

class CleanupService:
    """
    Automatic resource cleanup service.

    Cleans:
    - Temp files older than 1 hour
    - Expired working memory tasks
    - Closed MCP connections
    - Old execution logs (optional)
    """

    def __init__(
        self,
        temp_dir: Path,
        db: AdaptiveDatabase,
        mcp_manager: MCPManager,
        working_memory: WorkingMemory
    ):
        self.temp_dir = temp_dir
        self.db = db
        self.mcp_manager = mcp_manager
        self.working_memory = working_memory
        self._cleanup_interval = 300  # 5 minutes
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start background cleanup task."""
        logger.info("Starting cleanup service")
        self._task = asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        """Stop cleanup service."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Cleanup service stopped")

    async def _cleanup_loop(self) -> None:
        """Periodic cleanup loop."""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self.cleanup_all()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}", exc_info=True)

    async def cleanup_all(self) -> None:
        """Run all cleanup tasks."""
        logger.info("Running cleanup tasks")

        await asyncio.gather(
            self._cleanup_temp_files(),
            self._cleanup_working_memory(),
            self._cleanup_mcp_connections(),
            return_exceptions=True
        )

        logger.info("Cleanup completed")

    async def _cleanup_temp_files(self) -> None:
        """Delete temp files older than 1 hour."""
        try:
            cutoff = datetime.utcnow() - timedelta(hours=1)
            deleted_count = 0

            for file_path in self.temp_dir.glob("**/*"):
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)

                    if file_time < cutoff:
                        try:
                            file_path.unlink()
                            deleted_count += 1
                        except Exception as e:
                            logger.warning(f"Failed to delete {file_path}: {e}")

            if deleted_count > 0:
                logger.info(f"Deleted {deleted_count} temp files")

        except Exception as e:
            logger.error(f"Temp file cleanup failed: {e}", exc_info=True)

    async def _cleanup_working_memory(self) -> None:
        """Delete expired working memory tasks."""
        try:
            expired_count = await self.working_memory.cleanup_expired_tasks(
                older_than_hours=24
            )

            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired working memory tasks")

        except Exception as e:
            logger.error(f"Working memory cleanup failed: {e}", exc_info=True)

    async def _cleanup_mcp_connections(self) -> None:
        """Close idle MCP connections."""
        try:
            closed_count = await self.mcp_manager.close_idle_connections(
                idle_timeout_minutes=30
            )

            if closed_count > 0:
                logger.info(f"Closed {closed_count} idle MCP connections")

        except Exception as e:
            logger.error(f"MCP connection cleanup failed: {e}", exc_info=True)
```

### 4. Performance Monitoring

**Middleware Performance Tracking**:

```python
# middleware/performance_monitor.py

from langchain.agents.middleware import BaseMiddleware
from typing import Dict, Any, Optional
from datetime import datetime
import time
import logging

logger = logging.getLogger(__name__)

class PerformanceMonitorMiddleware(BaseMiddleware):
    """
    Performance monitoring for agent execution.

    Tracks:
    - Total execution time
    - Per-node execution time
    - Tool call latencies
    - Database query times
    - Context retrieval times
    """

    def __init__(self):
        self._start_time: Optional[float] = None
        self._node_timings: Dict[str, float] = {}
        self._tool_timings: Dict[str, List[float]] = {}

    async def before_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Start performance tracking."""
        self._start_time = time.time()
        self._node_timings = {}
        self._tool_timings = {}

        state["performance_metrics"] = {
            "started_at": datetime.utcnow().isoformat()
        }

        return state

    async def before_node(self, node_name: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Track node start."""
        state[f"_node_start_{node_name}"] = time.time()
        return state

    async def after_node(self, node_name: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Track node completion."""
        start_key = f"_node_start_{node_name}"

        if start_key in state:
            duration = time.time() - state[start_key]
            self._node_timings[node_name] = duration
            del state[start_key]

        return state

    async def before_tool(self, tool_name: str, arguments: dict) -> dict:
        """Track tool call start."""
        return {
            "tool_name": tool_name,
            "start_time": time.time()
        }

    async def after_tool(
        self,
        tool_name: str,
        result: Any,
        start_time: float,
        error: Optional[Exception] = None
    ) -> dict:
        """Track tool call completion."""
        duration = time.time() - start_time

        if tool_name not in self._tool_timings:
            self._tool_timings[tool_name] = []

        self._tool_timings[tool_name].append(duration)

        return {"duration_ms": int(duration * 1000)}

    async def after_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Complete performance tracking."""
        if not self._start_time:
            return state

        total_duration = time.time() - self._start_time

        # Calculate statistics
        metrics = {
            "total_duration_ms": int(total_duration * 1000),
            "completed_at": datetime.utcnow().isoformat(),
            "node_timings_ms": {
                node: int(duration * 1000)
                for node, duration in self._node_timings.items()
            },
            "tool_timings_ms": {
                tool: {
                    "calls": len(timings),
                    "total": int(sum(timings) * 1000),
                    "avg": int(sum(timings) / len(timings) * 1000),
                    "max": int(max(timings) * 1000),
                    "min": int(min(timings) * 1000)
                }
                for tool, timings in self._tool_timings.items()
            }
        }

        state["performance_metrics"].update(metrics)

        # Log performance if slow
        if total_duration > 5.0:
            logger.warning(
                f"Slow execution detected: {total_duration:.2f}s",
                extra={"metrics": metrics}
            )

        return state
```

### 5. Structured Logging with Correlation

**Correlation ID Tracking**:

```python
# middleware/correlation_middleware.py

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
from uuid import uuid4
import contextvars
import logging

# Context variable for correlation ID
correlation_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "correlation_id",
    default=None
)

class CorrelationMiddleware(BaseHTTPMiddleware):
    """
    Add correlation ID to all requests.

    Correlation ID flows through:
    - HTTP headers
    - Logs
    - Database records
    - External API calls
    """

    async def dispatch(self, request: Request, call_next):
        # Extract or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))

        # Store in context variable
        correlation_id_var.set(correlation_id)

        # Add to request state
        request.state.correlation_id = correlation_id

        # Process request
        response = await call_next(request)

        # Add to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        return response


# Structured logging with correlation
class CorrelationFilter(logging.Filter):
    """Add correlation ID to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        correlation_id = correlation_id_var.get()
        record.correlation_id = correlation_id or "NO_CORRELATION_ID"
        return True


# Configure logging
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "correlation_id": "%(correlation_id)s", "module": "%(name)s", "message": "%(message)s"}',
            "datefmt": "%Y-%m-%dT%H:%M:%S%z"
        }
    },
    "filters": {
        "correlation": {
            "()": CorrelationFilter
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "json",
            "filters": ["correlation"],
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "json",
            "filters": ["correlation"],
            "filename": "logs/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"]
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
```

## Implementation Boundaries for AI

### Files to CREATE:

```
src/agent_workbench/api/routes/
├── health.py                        # Health check endpoints

src/agent_workbench/middleware/
├── error_boundary.py                # Error boundaries and recovery
├── rate_limiter.py                  # Token bucket rate limiting
├── performance_monitor.py           # Performance tracking middleware
└── correlation_middleware.py        # Correlation ID tracking

src/agent_workbench/services/
├── cleanup_service.py               # Resource cleanup service
└── analytics_service.py             # Query execution logs and metrics

src/agent_workbench/monitoring/
├── metrics.py                       # Performance metrics collection
├── alerts.py                        # Alert definitions and hooks
└── resource_monitor.py              # System resource monitoring
```

### Files to MODIFY:

```
src/agent_workbench/main.py                      # Register middleware, health endpoint
src/agent_workbench/services/agent_service.py    # Add health check method
src/agent_workbench/services/mcp_manager.py      # Add health check, connection pooling
src/agent_workbench/database/backends/sqlite.py  # Add connection pool management
src/agent_workbench/database/backends/hub.py     # Add connection pool management
```

### Exact Function Signatures:

```python
# CREATE: api/routes/health.py
class ServiceStatus(BaseModel):
    name: str
    status: str
    latency_ms: Optional[int]
    message: Optional[str]
    timestamp: datetime

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    services: List[ServiceStatus]
    resources: Dict[str, Any]

@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse

async def check_database_health() -> ServiceStatus
async def check_agent_health() -> ServiceStatus
async def check_mcp_health() -> ServiceStatus
async def check_middleware_health() -> ServiceStatus
def get_resource_usage() -> Dict[str, Any]

# CREATE: middleware/error_boundary.py
class ErrorBoundaryMiddleware(BaseMiddleware):
    def __init__(self, max_retries: int = 3, fallback_enabled: bool = True)
    async def before_agent(self, state: Dict[str, Any]) -> Dict[str, Any]
    async def on_error(self, error: Exception, state: Dict[str, Any]) -> Dict[str, Any]
    def _is_retryable_error(self, error: Exception) -> bool
    def _get_fallback_response(self, error: Exception, state: Dict[str, Any]) -> str

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse

# CREATE: middleware/rate_limiter.py
class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float)
    async def consume(self, tokens: int = 1) -> bool
    def _refill(self) -> None

class RateLimiter:
    def __init__(self)
    async def check_rate_limit(self, user_id: str) -> None
    async def release(self, user_id: str) -> None

async def rate_limit_middleware(request: Request, call_next)

# CREATE: middleware/performance_monitor.py
class PerformanceMonitorMiddleware(BaseMiddleware):
    def __init__(self)
    async def before_agent(self, state: Dict[str, Any]) -> Dict[str, Any]
    async def before_node(self, node_name: str, state: Dict[str, Any]) -> Dict[str, Any]
    async def after_node(self, node_name: str, state: Dict[str, Any]) -> Dict[str, Any]
    async def before_tool(self, tool_name: str, arguments: dict) -> dict
    async def after_tool(self, tool_name: str, result: Any, start_time: float, error: Optional[Exception] = None) -> dict
    async def after_agent(self, state: Dict[str, Any]) -> Dict[str, Any]

# CREATE: middleware/correlation_middleware.py
correlation_id_var: contextvars.ContextVar[Optional[str]]

class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next)

class CorrelationFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool

# CREATE: services/cleanup_service.py
class CleanupService:
    def __init__(self, temp_dir: Path, db: AdaptiveDatabase, mcp_manager: MCPManager, working_memory: WorkingMemory)
    async def start(self) -> None
    async def stop(self) -> None
    async def cleanup_all(self) -> None
    async def _cleanup_temp_files(self) -> None
    async def _cleanup_working_memory(self) -> None
    async def _cleanup_mcp_connections(self) -> None

# CREATE: services/analytics_service.py
class AnalyticsService:
    def __init__(self, db: AdaptiveDatabase)
    def get_conversation_executions(self, conversation_id: UUID, limit: int = 50) -> List[AgentExecutionLogModel]
    def get_user_errors(self, user_id: UUID, since: datetime = None, limit: int = 100) -> List[AgentExecutionLogModel]
    def get_system_errors(self, since: datetime = None, limit: int = 100) -> List[AgentExecutionLogModel]
    def get_execution_tool_calls(self, execution_log_id: UUID) -> List[ToolCallLogModel]
    def get_slowest_tools(self, limit: int = 20) -> List[Dict[str, Any]]
    def get_model_performance(self, provider: str = None, since: datetime = None) -> List[Dict[str, Any]]
    def get_expensive_executions(self, threshold_usd: float = 0.10, limit: int = 50) -> List[AgentExecutionLogModel]
    def get_slow_executions(self, threshold_ms: int = 10000, limit: int = 50) -> List[AgentExecutionLogModel]
    def get_user_tool_usage(self, user_id: UUID, since: datetime = None) -> List[Dict[str, Any]]

# CREATE: monitoring/metrics.py
class MetricsCollector:
    def __init__(self)
    def record_request(self, endpoint: str, duration_ms: int, status_code: int) -> None
    def record_agent_execution(self, duration_ms: int, token_count: int, cost: float) -> None
    def record_tool_call(self, tool_name: str, duration_ms: int, success: bool) -> None
    def get_metrics_summary(self, time_window_minutes: int = 60) -> Dict[str, Any]

# CREATE: monitoring/resource_monitor.py
class ResourceMonitor:
    def __init__(self)
    async def start_monitoring(self) -> None
    async def stop_monitoring(self) -> None
    def get_current_usage(self) -> Dict[str, Any]
    def get_usage_history(self, time_window_minutes: int = 60) -> List[Dict[str, Any]]

# MODIFY: services/agent_service.py
class AgentService:
    async def health_check(self) -> HealthCheckResponse  # ADD
    async def _check_model_connectivity(self) -> bool    # ADD

# MODIFY: services/mcp_manager.py
class MCPManager:
    async def check_all_servers(self) -> List[Dict[str, str]]  # ADD
    async def close_idle_connections(self, idle_timeout_minutes: int = 30) -> int  # ADD

# MODIFY: database/backends/sqlite.py
class SQLiteBackend(DatabaseBackend):
    def __init__(self, connection_string: str, pool_size: int = 10)  # MODIFY: Add pool_size
    async def health_check(self) -> bool  # ADD

# MODIFY: main.py
# ADD middleware registration
app.add_middleware(CorrelationMiddleware)
app.middleware("http")(rate_limit_middleware)
app.add_exception_handler(Exception, global_exception_handler)

# ADD cleanup service
cleanup_service: Optional[CleanupService] = None

@app.on_event("startup")
async def startup():
    global cleanup_service
    cleanup_service = CleanupService(...)
    await cleanup_service.start()

@app.on_event("shutdown")
async def shutdown():
    if cleanup_service:
        await cleanup_service.stop()
```

### Additional Dependencies:

```toml
# Production monitoring
psutil = "^5.9.0"              # System resource monitoring
tenacity = "^8.2.0"            # Retry with exponential backoff

# Already in project (verify versions)
# httpx, openai, anthropic, sqlalchemy, fastapi
```

### FORBIDDEN Actions:

- Implementing external monitoring services (Prometheus, Grafana)
- Adding distributed tracing (OpenTelemetry)
- Implementing advanced caching (Redis, Memcached)
- Adding load balancing or horizontal scaling
- Implementing Kubernetes-specific features
- Adding frontend performance optimization
- Implementing CDN integration
- Adding WAF or DDoS protection

## Testing Strategy

### Test Coverage Requirements: ~8 comprehensive tests

```python
# tests/integration/test_production_hardening.py

import pytest
from fastapi.testclient import TestClient
import asyncio
import time

class TestHealthChecks:
    """Test health check system."""

    def test_health_endpoint_returns_200(self, client: TestClient):
        """Health endpoint returns 200 with all services healthy."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert len(data["services"]) >= 4  # database, agent, mcp, middleware
        assert all(s["status"] == "healthy" for s in data["services"])

    def test_health_check_includes_resource_usage(self, client: TestClient):
        """Health check includes system resource metrics."""
        response = client.get("/health")
        data = response.json()

        assert "resources" in data
        assert "memory_percent" in data["resources"]
        assert "cpu_percent" in data["resources"]
        assert "disk_usage_percent" in data["resources"]

    async def test_database_health_check_detects_failure(self, db):
        """Database health check detects connection failure."""
        # Simulate database failure
        await db.close()

        status = await check_database_health()
        assert status.status == "unhealthy"
        assert "failed" in status.message.lower()


class TestErrorBoundaries:
    """Test error handling and recovery."""

    async def test_retryable_error_triggers_retry(self, agent_service):
        """Retryable errors (network, rate limit) trigger automatic retry."""
        # Mock network error
        with patch.object(agent_service, "_call_model", side_effect=[
            TimeoutError("Connection timeout"),
            TimeoutError("Connection timeout"),
            "Success response"
        ]):
            response = await agent_service.execute(...)

            assert response.success
            assert response.retry_count == 2

    async def test_non_retryable_error_uses_fallback(self, agent_service):
        """Non-retryable errors return fallback response."""
        with patch.object(agent_service, "_call_model", side_effect=ValueError("Invalid input")):
            response = await agent_service.execute(...)

            assert not response.success
            assert "unexpected issue" in response.content.lower()

    def test_global_error_handler_catches_unhandled_exceptions(self, client: TestClient):
        """Global error handler catches all unhandled exceptions."""
        # Trigger unhandled exception
        response = client.post("/api/v1/test/error")

        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert "timestamp" in data


class TestRateLimiting:
    """Test rate limiting system."""

    async def test_rate_limit_blocks_excessive_requests(self, client: TestClient, auth_headers):
        """Rate limiter blocks requests exceeding limit."""
        # Send 70 requests (limit is 60/minute)
        responses = []
        for _ in range(70):
            response = client.post("/api/v1/chat/workflow", headers=auth_headers, json={...})
            responses.append(response.status_code)

        # First 60 should succeed, rest should be rate limited
        assert responses[:60].count(200) == 60
        assert responses[60:].count(429) == 10

    async def test_concurrent_request_limit_enforced(self, client: TestClient, auth_headers):
        """Concurrent request limit is enforced per user."""
        # Start 7 concurrent requests (limit is 5)
        async def make_request():
            return client.post("/api/v1/chat/workflow", headers=auth_headers, json={...})

        results = await asyncio.gather(*[make_request() for _ in range(7)], return_exceptions=True)

        # 5 should succeed, 2 should be rate limited
        success_count = sum(1 for r in results if r.status_code == 200)
        rate_limited_count = sum(1 for r in results if r.status_code == 429)

        assert success_count == 5
        assert rate_limited_count == 2


class TestResourceCleanup:
    """Test automatic resource cleanup."""

    async def test_temp_files_cleaned_automatically(self, cleanup_service, tmp_path):
        """Temp files older than 1 hour are deleted."""
        # Create old temp file
        old_file = tmp_path / "old_file.txt"
        old_file.write_text("test")

        # Set modification time to 2 hours ago
        two_hours_ago = time.time() - (2 * 60 * 60)
        os.utime(old_file, (two_hours_ago, two_hours_ago))

        # Run cleanup
        await cleanup_service._cleanup_temp_files()

        # File should be deleted
        assert not old_file.exists()

    async def test_expired_working_memory_cleaned(self, cleanup_service, working_memory):
        """Expired working memory tasks are cleaned."""
        # Create expired task
        task_id = await working_memory.create_task()

        # Manually expire it
        await working_memory._expire_task(task_id)

        # Run cleanup
        await cleanup_service._cleanup_working_memory()

        # Task should be deleted
        with pytest.raises(ValueError):
            await working_memory.get_task(task_id)


class TestPerformanceMonitoring:
    """Test performance tracking."""

    async def test_performance_metrics_collected(self, agent_service):
        """Performance metrics are collected during execution."""
        response = await agent_service.execute(...)

        assert "performance_metrics" in response.metadata
        metrics = response.metadata["performance_metrics"]

        assert "total_duration_ms" in metrics
        assert "node_timings_ms" in metrics
        assert "tool_timings_ms" in metrics

    async def test_slow_execution_logged(self, agent_service, caplog):
        """Slow executions (>5s) are logged as warnings."""
        # Mock slow execution
        with patch.object(agent_service, "_call_model", side_effect=lambda *args: asyncio.sleep(6)):
            await agent_service.execute(...)

        # Check warning logged
        assert "Slow execution detected" in caplog.text


class TestCorrelationTracking:
    """Test correlation ID tracking."""

    def test_correlation_id_flows_through_request(self, client: TestClient):
        """Correlation ID flows through entire request."""
        correlation_id = "test-correlation-123"

        response = client.post(
            "/api/v1/chat/workflow",
            headers={"X-Correlation-ID": correlation_id},
            json={...}
        )

        # Response should include same correlation ID
        assert response.headers["X-Correlation-ID"] == correlation_id

    def test_correlation_id_generated_if_missing(self, client: TestClient):
        """Correlation ID is generated if not provided."""
        response = client.post("/api/v1/chat/workflow", json={...})

        # Response should include generated correlation ID
        assert "X-Correlation-ID" in response.headers
        assert len(response.headers["X-Correlation-ID"]) > 0


# Performance tests
class TestPerformanceUnderLoad:
    """Test system performance under load."""

    @pytest.mark.slow
    async def test_concurrent_requests_handled(self, client: TestClient, auth_headers):
        """System handles 20 concurrent requests."""
        async def make_request():
            return client.post("/api/v1/chat/workflow", headers=auth_headers, json={
                "message": "Test message",
                "conversation_id": None
            })

        start = time.time()
        results = await asyncio.gather(*[make_request() for _ in range(20)])
        duration = time.time() - start

        # All should succeed
        assert all(r.status_code == 200 for r in results)

        # Should complete in reasonable time (<30s for 20 requests)
        assert duration < 30

    @pytest.mark.slow
    def test_memory_usage_stable_under_load(self, client: TestClient, auth_headers):
        """Memory usage remains stable under sustained load."""
        import psutil
        process = psutil.Process()

        initial_memory = process.memory_info().rss / (1024 * 1024)  # MB

        # Send 100 requests
        for _ in range(100):
            client.post("/api/v1/chat/workflow", headers=auth_headers, json={...})

        final_memory = process.memory_info().rss / (1024 * 1024)  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be < 100MB
        assert memory_increase < 100
```

## Success Criteria

### Functional Requirements:
- [ ] **Health Checks**: `/health` endpoint returns comprehensive service status
- [ ] **Database Health**: Connection and query latency monitored
- [ ] **Agent Health**: Model connectivity verified
- [ ] **MCP Health**: Server connection status tracked
- [ ] **Resource Metrics**: Memory, CPU, disk usage included

### Error Handling:
- [ ] **Global Error Handler**: All unhandled exceptions caught
- [ ] **Error Boundaries**: LangGraph errors don't crash application
- [ ] **Retry Logic**: Retryable errors (network, rate limit) trigger automatic retry
- [ ] **Fallback Responses**: Non-retryable errors return user-friendly messages
- [ ] **Error Logging**: All errors logged with stack traces and context

### Rate Limiting:
- [ ] **Per-User Rate Limit**: 60 requests per minute per user
- [ ] **Concurrent Limit**: Max 5 concurrent requests per user
- [ ] **Token Bucket**: Rate limiting uses token bucket algorithm
- [ ] **Graceful Rejection**: Rate-limited requests return 429 with Retry-After header

### Resource Management:
- [ ] **Temp File Cleanup**: Files older than 1 hour automatically deleted
- [ ] **Working Memory Cleanup**: Expired tasks (>24 hours) removed
- [ ] **MCP Connection Cleanup**: Idle connections (>30 min) closed
- [ ] **Database Connections**: Connection pooling with max pool size
- [ ] **Cleanup Service**: Background cleanup runs every 5 minutes

### Performance:
- [ ] **Performance Monitoring**: Middleware tracks execution times
- [ ] **Node Timing**: Per-node execution time recorded
- [ ] **Tool Timing**: Per-tool call latency tracked
- [ ] **Slow Execution Alerts**: Executions >5s logged as warnings
- [ ] **Metrics API**: Analytics service provides performance queries

### Observability:
- [ ] **Correlation IDs**: All requests tagged with correlation ID
- [ ] **Structured Logging**: Logs in JSON format with correlation ID
- [ ] **Request Tracing**: Full request flow traceable via correlation ID
- [ ] **Log Rotation**: Log files rotated at 10MB (5 backups)

### Stability:
- [ ] **Concurrent Requests**: System handles 20+ concurrent requests
- [ ] **Memory Stability**: Memory usage stable under sustained load
- [ ] **No Crashes**: Application survives all error conditions
- [ ] **Graceful Shutdown**: All resources cleaned on shutdown

### Testing:
- [ ] **>90% test coverage** for production hardening features
- [ ] **8+ integration tests** covering all hardening components
- [ ] **Performance tests** validate system under load
- [ ] **Error injection tests** verify recovery mechanisms

---

## Notes

**Critical Success Factor**: This is the FINAL phase before v0.2.0 release. All stability, monitoring, and reliability features MUST be production-ready.

**Dependencies**: This phase requires ALL Phase 2 components (2.1-2.7) to be complete and working.

**Production Readiness**: After this phase, the system should be deployable to production with confidence in stability, observability, and error recovery.
