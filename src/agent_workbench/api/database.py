"""Database session management for Agent Workbench API."""

from typing import AsyncGenerator, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from agent_workbench.models.config import DatabaseConfig
from agent_workbench.models.database import Base


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[sessionmaker[AsyncSession]] = None

    async def initialize(self) -> None:
        """Initialize the database engine and session factory."""
        if self.engine is not None:
            return

        # Create async engine
        # SQLite doesn't support pool_size, max_overflow, pool_timeout
        if "sqlite" in self.config.database_url.lower():
            self.engine = create_async_engine(
                self.config.database_url,
                echo=self.config.echo_sql,
                pool_recycle=self.config.pool_recycle,
            )
        else:
            self.engine = create_async_engine(
                self.config.database_url,
                echo=self.config.echo_sql,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
            )

        # Create session factory
        self.session_factory = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def close(self) -> None:
        """Close the database engine."""
        if self.engine is not None:
            await self.engine.dispose()
            self.engine = None
            self.session_factory = None

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session dependency."""
        if self.session_factory is None:
            await self.initialize()

        # Add assertion to help mypy understand that session_factory is not None
        assert self.session_factory is not None, "Session factory should be initialized"

        async with self.session_factory() as session:
            try:
                yield session
            except SQLAlchemyError:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def create_tables(self) -> None:
        """Create all tables defined in the models."""
        if self.engine is None:
            await self.initialize()

        if self.engine is not None:
            async with self.engine.begin() as conn:
                assert Base is not None
                await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self) -> None:
        """Drop all tables (for testing)."""
        if self.engine is None:
            await self.initialize()

        if self.engine is not None:
            async with self.engine.begin() as conn:
                assert Base is not None
                await conn.run_sync(Base.metadata.drop_all)

    async def check_database_connection(self) -> bool:
        """Check if database is accessible."""
        # If engine was explicitly closed, don't auto-reinitialize
        if self.engine is None and self.session_factory is None:
            return False

        try:
            if self.engine is None:
                await self.initialize()

            if self.engine is not None:
                from sqlalchemy import text

                async with self.engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
                return True
            return False
        except Exception as e:
            print(f"Database connection check failed: {e}")
            return False


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


async def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        # Load configuration (in real app, this would come from settings)
        config = DatabaseConfig()
        _db_manager = DatabaseManager(config)
        await _db_manager.initialize()
    return _db_manager


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for getting database sessions."""
    db_manager = await get_database_manager()
    async for session in db_manager.get_session():
        yield session


async def init_database() -> None:
    """Initialize the database."""
    db_manager = await get_database_manager()
    await db_manager.create_tables()


async def close_database() -> None:
    """Close the database connection."""
    global _db_manager
    if _db_manager is not None:
        await _db_manager.close()
        _db_manager = None


# Health check utilities
async def check_database_connection() -> bool:
    """Check if database is accessible."""
    try:
        db_manager = await get_database_manager()
        if db_manager.engine is None:
            return False

        from sqlalchemy import text

        async with db_manager.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
