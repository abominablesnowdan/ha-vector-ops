from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_URL
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import VectorOpsApi, VectorOpsApiError
from .const import DEFAULT_URL, DOMAIN


class VectorOpsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            url = user_input[CONF_URL].rstrip("/")
            await self.async_set_unique_id("vector_ops")
            self._abort_if_unique_id_configured()
            try:
                await VectorOpsApi(async_get_clientsession(self.hass), url).async_snapshot()
            except VectorOpsApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title="Vector Ops", data={CONF_URL: url})
        schema = vol.Schema({vol.Required(CONF_URL, default=DEFAULT_URL): str})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
