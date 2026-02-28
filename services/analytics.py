from __future__ import annotations

import asyncio
import logging

import httpx

from config import API_SECRET, MEASUREMENT_ID

logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None
        self._tasks: set[asyncio.Task[None]] = set()

    @property
    def is_enabled(self) -> bool:
        return bool(MEASUREMENT_ID and API_SECRET)

    async def initialize(self) -> None:
        if self.is_enabled and self._client is None:
            self._client = httpx.AsyncClient(timeout=5.0)

    async def close(self) -> None:
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
            self._tasks.clear()

        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def queue_event(self, user_id: int, user_lang_code: str | None, action_name: str) -> None:
        if not self.is_enabled:
            return

        task = asyncio.create_task(
            self.send_event(user_id=user_id, user_lang_code=user_lang_code, action_name=action_name)
        )
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def send_event(self, user_id: int, user_lang_code: str | None, action_name: str) -> None:
        if not self.is_enabled:
            return

        if self._client is None:
            await self.initialize()

        if self._client is None:
            return

        payload = {
            "client_id": str(user_id),
            "user_id": str(user_id),
            "events": [
                {
                    "name": action_name,
                    "params": {
                        "language": user_lang_code or "unknown",
                        "session_id": str(user_id),
                        "engagement_time_msec": "100",
                    },
                }
            ],
        }

        try:
            await self._client.post(
                "https://www.google-analytics.com/mp/collect",
                params={
                    "measurement_id": MEASUREMENT_ID,
                    "api_secret": API_SECRET,
                },
                json=payload,
            )
        except httpx.HTTPError:
            logger.warning("Failed to send analytics event '%s' for user %s", action_name, user_id)


analytics = AnalyticsService()
