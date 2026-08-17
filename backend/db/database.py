# =============================================================================
# ArcZhiin — Database Manager
# Async SQLite connection manager with schema initialization.
# =============================================================================

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

import aiosqlite

from config import settings

logger = logging.getLogger(__name__)

# Path to the schema file
_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def generate_id() -> str:
    """Generate a unique ID for database records."""
    return str(uuid.uuid4())


class Database:
    """Async SQLite database manager."""

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path or settings.database.path
        self._connection: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        """Open the database connection and initialize schema."""
        db_dir = Path(self._db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        self._connection = await aiosqlite.connect(self._db_path)
        self._connection.row_factory = aiosqlite.Row

        # Enable WAL mode and foreign keys
        await self._connection.execute("PRAGMA journal_mode=WAL")
        await self._connection.execute("PRAGMA foreign_keys=ON")

        # Initialize schema
        await self._init_schema()

        logger.info("Database connected: %s", self._db_path)

    async def _init_schema(self) -> None:
        """Run the schema.sql file to create tables if they don't exist."""
        if not _SCHEMA_PATH.exists():
            logger.warning("Schema file not found: %s", _SCHEMA_PATH)
            return

        schema_sql = _SCHEMA_PATH.read_text()

        # Split by semicolon and execute each statement
        # (skip PRAGMA lines as they're already set above)
        for statement in schema_sql.split(";"):
            cleaned = statement.strip()
            if cleaned and not cleaned.startswith("PRAGMA") and not cleaned.startswith("#"):
                try:
                    await self._connection.execute(cleaned)
                except Exception as exc:
                    logger.debug("Schema statement skipped: %s", exc)

        await self._connection.commit()
        logger.info("Database schema initialized")

    async def disconnect(self) -> None:
        """Close the database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None
            logger.info("Database disconnected")

    @property
    def conn(self) -> aiosqlite.Connection:
        """Get the active connection (raises if not connected)."""
        if self._connection is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._connection

    async def execute(
        self, query: str, params: tuple[Any, ...] = ()
    ) -> aiosqlite.Cursor:
        """Execute a query and return the cursor."""
        return await self.conn.execute(query, params)

    async def fetch_one(
        self, query: str, params: tuple[Any, ...] = ()
    ) -> dict[str, Any] | None:
        """Execute a query and return a single row as a dict."""
        cursor = await self.execute(query, params)
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    async def fetch_all(
        self, query: str, params: tuple[Any, ...] = ()
    ) -> list[dict[str, Any]]:
        """Execute a query and return all rows as dicts."""
        cursor = await self.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def insert(self, query: str, params: tuple[Any, ...] = ()) -> str:
        """Execute an INSERT and return the last row ID."""
        cursor = await self.execute(query, params)
        await self.conn.commit()
        return str(cursor.lastrowid)

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self.conn.commit()


# Singleton instance
db = Database()
