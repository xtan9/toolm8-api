import logging
from typing import Optional, cast

from supabase import Client, create_client

from app.config import settings

logger = logging.getLogger(__name__)


class DatabaseConnection:
    def __init__(self) -> None:
        self._client: Optional[Client] = None

    def get_client(self) -> Client:
        if self._client is None:
            try:
                self._client = cast(
                    Client,
                    create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY),
                )
                logger.info("Supabase client created successfully")
            except Exception as e:
                logger.error(f"Failed to create Supabase client: {e}")
                raise
        return self._client


db_connection = DatabaseConnection()
