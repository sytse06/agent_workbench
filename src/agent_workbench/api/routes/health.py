"""Health check API routes for Agent Workbench."""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from agent_workbench.api.database import check_database_connection, get_session
from agent_workbench.models.schemas import HealthCheckResponse

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get(
    "/",
    response_model=HealthCheckResponse,
    summary="Health check",
    description="Check system health and database connectivity",
)
async def health_check(
    session: AsyncSession = Depends(get_session),
) -> HealthCheckResponse:
    """Health check endpoint."""
    # Check database connectivity
    database_connected = await check_database_connection()

    return HealthCheckResponse(
        status="healthy" if database_connected else "unhealthy",
        database_connected=database_connected,
        timestamp=datetime.utcnow(),
    )


@router.get(
    "/ping", summary="Ping", description="Simple ping endpoint for uptime monitoring"
)
async def ping() -> dict:
    """Simple ping endpoint."""
    return {"message": "pong", "timestamp": datetime.utcnow()}
