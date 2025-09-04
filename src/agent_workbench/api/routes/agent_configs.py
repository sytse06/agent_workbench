"""Agent configuration API routes for Agent Workbench."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from agent_workbench.api.database import get_session
from agent_workbench.api.exceptions import (
    AgentConfigConflictError,
    AgentConfigNotFoundError,
)
from agent_workbench.models.database import AgentConfigModel
from agent_workbench.models.schemas import (
    AgentConfigCreate,
    AgentConfigResponse,
    AgentConfigUpdate,
)

router = APIRouter(prefix="/api/v1/agent-configs", tags=["agent-configs"])


@router.post(
    "/",
    response_model=AgentConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create agent configuration",
    description="Create a new agent configuration",
)
async def create_agent_config(
    request: AgentConfigCreate, session: AsyncSession = Depends(get_session)
) -> AgentConfigResponse:
    """Create a new agent configuration."""
    # Check if config with same name already exists
    result = await session.execute(
        AgentConfigModel.__table__.select().where(AgentConfigModel.name == request.name)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise AgentConfigConflictError(
            f"Agent configuration with name '{request.name}' already exists"
        )

    agent_config = await AgentConfigModel.create(session, **request.model_dump())
    return AgentConfigResponse.model_validate(agent_config)


@router.get(
    "/{config_id}",
    response_model=AgentConfigResponse,
    summary="Get agent configuration",
    description="Get an agent configuration by ID",
)
async def get_agent_config(
    config_id: UUID, session: AsyncSession = Depends(get_session)
) -> AgentConfigResponse:
    """Get agent configuration by ID."""
    agent_config = await AgentConfigModel.get_by_id(session, config_id)
    if agent_config is None:
        raise AgentConfigNotFoundError(str(config_id))
    return AgentConfigResponse.model_validate(agent_config)


@router.get(
    "/",
    response_model=List[AgentConfigResponse],
    summary="List agent configurations",
    description="List all agent configurations",
)
async def list_agent_configs(
    session: AsyncSession = Depends(get_session),
) -> List[AgentConfigResponse]:
    """List agent configurations."""
    agent_configs = await AgentConfigModel.get_all(session)
    return [AgentConfigResponse.model_validate(config) for config in agent_configs]


@router.put(
    "/{config_id}",
    response_model=AgentConfigResponse,
    summary="Update agent configuration",
    description="Update an agent configuration by ID",
)
async def update_agent_config(
    config_id: UUID,
    request: AgentConfigUpdate,
    session: AsyncSession = Depends(get_session),
) -> AgentConfigResponse:
    """Update agent configuration."""
    agent_config = await AgentConfigModel.get_by_id(session, config_id)
    if agent_config is None:
        raise AgentConfigNotFoundError(str(config_id))

    # Check if new name conflicts with existing config
    if request.name and request.name != agent_config.name:
        result = await session.execute(
            AgentConfigModel.__table__.select()
            .where(AgentConfigModel.name == request.name)
            .where(AgentConfigModel.id != config_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise AgentConfigConflictError(
                f"Agent configuration with name '{request.name}' already exists"
            )

    update_data = request.model_dump(exclude_unset=True)
    updated_config = await agent_config.update(session, **update_data)
    return AgentConfigResponse.model_validate(updated_config)


@router.delete(
    "/{config_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete agent configuration",
    description="Delete an agent configuration by ID",
)
async def delete_agent_config(
    config_id: UUID, session: AsyncSession = Depends(get_session)
) -> None:
    """Delete agent configuration."""
    agent_config = await AgentConfigModel.get_by_id(session, config_id)
    if agent_config is None:
        raise AgentConfigNotFoundError(str(config_id))

    await agent_config.delete(session)
