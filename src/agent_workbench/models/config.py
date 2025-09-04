"""Database configuration for Agent Workbench."""

from pydantic import BaseModel, Field


class DatabaseConfig(BaseModel):
    """Configuration for database connection."""

    # Database URL (e.g., "postgresql+asyncpg://user:pass@localhost/db")
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/agent_workbench.db",
        description="Database connection URL",
    )

    # Connection pool settings
    pool_size: int = Field(default=10, description="Connection pool size")

    max_overflow: int = Field(default=20, description="Maximum overflow connections")

    pool_timeout: int = Field(default=30, description="Pool timeout in seconds")

    pool_recycle: int = Field(default=3600, description="Pool recycle time in seconds")

    # Echo SQL statements (for debugging)
    echo_sql: bool = Field(default=False, description="Echo SQL statements to stdout")

    # Future: Add more database-specific configurations
