from __future__ import annotations

from pathlib import Path

import voluptuous as vol
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import VectorOpsApi, VectorOpsApiError
from .const import DOMAIN, PLATFORMS
from .coordinator import VectorOpsCoordinator

ITEM_SCHEMA = vol.Schema({vol.Required("item_id"): cv.string})
BATCH_SCHEMA = vol.Schema({
    vol.Required("item_ids"): vol.All(cv.ensure_list, [cv.string], vol.Length(min=1)),
    vol.Optional("interval_minutes", default=10): vol.All(vol.Coerce(int), vol.Range(min=0, max=60)),
})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if not hass.data.get(DOMAIN, {}).get("static_paths_registered"):
        await hass.http.async_register_static_paths([
            StaticPathConfig(
                "/vector_ops_static/icons",
                str(Path(__file__).parent / "icons"),
                cache_headers=True,
            )
        ])
        hass.data.setdefault(DOMAIN, {})["static_paths_registered"] = True
    api = VectorOpsApi(async_get_clientsession(hass), entry.data[CONF_URL])
    coordinator = VectorOpsCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    if not hass.services.has_service(DOMAIN, "refresh_updates"):
        _register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not [key for key in hass.data[DOMAIN] if key != "static_paths_registered"]:
            for service in ("refresh_updates", "add_to_queue", "update_now", "update_batch", "run_pending", "clear_queue"):
                hass.services.async_remove(DOMAIN, service)
    return ok


def _register_services(hass: HomeAssistant) -> None:
    def coordinator() -> VectorOpsCoordinator:
        entries = [value for value in hass.data.get(DOMAIN, {}).values() if isinstance(value, VectorOpsCoordinator)]
        if not entries:
            raise HomeAssistantError("Vector Ops is not configured")
        return entries[0]

    async def invoke(call: ServiceCall) -> None:
        coord = coordinator()
        try:
            if call.service == "refresh_updates":
                await coord.api.async_refresh()
            elif call.service == "add_to_queue":
                await coord.api.async_queue(call.data["item_id"], False)
            elif call.service == "update_now":
                await coord.api.async_queue(call.data["item_id"], True)
            elif call.service == "update_batch":
                await coord.api.async_batch(call.data["item_ids"], call.data["interval_minutes"])
            elif call.service == "run_pending":
                await coord.api.async_run_pending()
            elif call.service == "clear_queue":
                await coord.api.async_clear_queue()
        except VectorOpsApiError as err:
            raise HomeAssistantError(str(err)) from err
        await coord.async_request_refresh()

    hass.services.async_register(DOMAIN, "refresh_updates", invoke)
    hass.services.async_register(DOMAIN, "add_to_queue", invoke, schema=ITEM_SCHEMA)
    hass.services.async_register(DOMAIN, "update_now", invoke, schema=ITEM_SCHEMA)
    hass.services.async_register(DOMAIN, "update_batch", invoke, schema=BATCH_SCHEMA)
    hass.services.async_register(DOMAIN, "run_pending", invoke)
    hass.services.async_register(DOMAIN, "clear_queue", invoke)
