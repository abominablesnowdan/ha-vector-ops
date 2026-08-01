from __future__ import annotations

from typing import Any

from aiohttp import ClientError, ClientSession


class VectorOpsApiError(Exception):
    pass


class VectorOpsApi:
    def __init__(self, session: ClientSession, base_url: str) -> None:
        self._session = session
        self.base_url = base_url.rstrip("/")

    async def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            async with self._session.request(method, self.base_url + path, json=payload, timeout=20) as response:
                data = await response.json(content_type=None)
                if response.status >= 400:
                    raise VectorOpsApiError(data.get("message") or f"Vector Ops returned HTTP {response.status}")
                return data
        except VectorOpsApiError:
            raise
        except (ClientError, TimeoutError, ValueError) as err:
            raise VectorOpsApiError(str(err)) from err

    async def async_snapshot(self) -> dict[str, Any]:
        return await self._request("GET", "/api/updates")

    async def async_status(self) -> dict[str, Any]:
        return await self._request("GET", "/api/status")

    async def async_refresh(self) -> dict[str, Any]:
        return await self._request("POST", "/api/updates/refresh", {})

    async def async_queue(self, item_id: str, start: bool) -> dict[str, Any]:
        return await self._request("POST", "/api/action/update-batch", {"items": [item_id], "interval_minutes": 0, "start": start})

    async def async_run_pending(self) -> dict[str, Any]:
        return await self._request("POST", "/api/action/resume-queue", {})

    async def async_clear_queue(self) -> dict[str, Any]:
        return await self._request("POST", "/api/action/clear-queue", {})
