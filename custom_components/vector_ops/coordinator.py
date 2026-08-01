from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import VectorOpsApi, VectorOpsApiError


class VectorOpsCoordinator(DataUpdateCoordinator[dict]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: VectorOpsApi) -> None:
        self.entry = entry
        self.api = api
        super().__init__(hass, logger=__import__("logging").getLogger(__name__), name="Vector Ops", update_interval=timedelta(seconds=30))

    async def _async_update_data(self) -> dict:
        try:
            return await self.api.async_snapshot()
        except VectorOpsApiError as err:
            raise UpdateFailed(str(err)) from err
