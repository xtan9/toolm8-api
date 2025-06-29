import asyncpg
from supabase import create_client, Client
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class DatabaseConnection:
    def __init__(self):
        self.supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        self._pool = None

    async def get_pool(self):
        if self._pool is None:
            try:
                self._pool = await asyncpg.create_pool(
                    settings.DATABASE_URL, min_size=5, max_size=20
                )
                logger.info("Database pool created successfully")
            except Exception as e:
                logger.error(f"Failed to create database pool: {e}")
                raise
        return self._pool

    async def close_pool(self):
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Database pool closed")


db_connection = DatabaseConnection()
