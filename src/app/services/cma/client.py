from __future__ import annotations

from typing import Any

import httpx

from ...core.config import settings


class CMAClient:
    def __init__(
        self,
        base_url: str = settings.CMA_API_BASE_URL,
        api_key: str = settings.CMA_API_KEY,
        timeout: int = settings.CMA_API_TIMEOUT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    async def post(self, path: str, json_body: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._headers(),
            timeout=self.timeout,
        ) as client:
            response = await client.post(path, json=json_body)
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
