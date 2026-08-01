from __future__ import annotations

from datetime import datetime, timedelta, timezone
import asyncio

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import VectorOpsApi


class VectorOpsCoordinator(DataUpdateCoordinator[dict]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: VectorOpsApi) -> None:
        self.entry = entry
        self.api = api
        super().__init__(hass, logger=__import__("logging").getLogger(__name__), name="Vector Ops", update_interval=timedelta(seconds=60))

    async def _async_update_data(self) -> dict:
        updates_result, overview_result = await asyncio.gather(
            self.api.async_snapshot(), self.api.async_status(), return_exceptions=True
        )
        errors: dict[str, str] = {}
        data = dict(self.data or {})
        if isinstance(updates_result, Exception):
            errors["updates"] = str(updates_result)
        else:
            data.update(updates_result)
        if isinstance(overview_result, Exception):
            errors["overview"] = str(overview_result)
        else:
            data["overview"] = overview_result
        if len(errors) == 2:
            raise UpdateFailed("; ".join(f"{key}: {value}" for key, value in errors.items()))
        data["_errors"] = errors
        data["_updated_at"] = datetime.now(timezone.utc).isoformat()
        return data
