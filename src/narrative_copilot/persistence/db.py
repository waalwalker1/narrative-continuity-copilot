"""
Database connection and session factory using SQLAlchemy and SQLite.
"""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from narrative_copilot.persistence.models import Base

DEFAULT_DB_URL = "sqlite+aiosqlite:///./narrative_copilot.db"


class Database:
    def __init__(self, db_url: str | None = None) -> None:
        url_str: str = db_url or os.getenv("DATABASE_URL") or DEFAULT_DB_URL
        # Handle SQLite file path conversion for async
        if url_str.startswith("sqlite:///"):
            url_str = url_str.replace("sqlite:///", "sqlite+aiosqlite:///")
        self.db_url: str = url_str

        self.engine: AsyncEngine = create_async_engine(
            self.db_url,
            echo=False,
            future=True,
        )
        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )

    async def init_db(self) -> None:
        """Create all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Yield async database session (for FastAPI dependency)."""
        async with self.session_factory() as session:
            yield session

    @asynccontextmanager
    async def session_scope(self) -> AsyncGenerator[AsyncSession, None]:
        """Context manager yielding async database session for tests and scripts."""
        async with self.session_factory() as session:
            yield session
