from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import HTTPException

from ...schemas.cma import (
    ComparablesResponse,
    ReportRequest,
    ReportResponse,
)

from .client import CMAClient

logger = logging.getLogger(__name__)


class CMAService:
    def __init__(self) -> None:
        self.client = CMAClient()

    async def find_comparables(self, body: dict[str, Any]) -> ComparablesResponse:
        try:
            data = await self.client.post("/api/v1/comparables", body)
        except httpx.HTTPStatusError as exc:
            detail = _extract_detail(exc)
            raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc
        except httpx.RequestError as exc:
            logger.exception("CMA API connection error")
            raise HTTPException(status_code=502, detail="CMA service unavailable") from exc
        return ComparablesResponse.model_validate(data)

    async def generate_report(self, request: ReportRequest) -> ReportResponse:
        body = request.model_dump(exclude_none=True)
        try:
            data = await self.client.post("/api/v1/reports", body)
        except httpx.HTTPStatusError as exc:
            detail = _extract_detail(exc)
            raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc
        except httpx.RequestError as exc:
            logger.exception("CMA API connection error")
            raise HTTPException(status_code=502, detail="CMA service unavailable") from exc

        return ReportResponse.model_validate(data)


def _extract_detail(exc: httpx.HTTPStatusError) -> str:
    try:
        return exc.response.json().get("detail", exc.response.text)
    except Exception:
        return exc.response.text


cma_service = CMAService()
