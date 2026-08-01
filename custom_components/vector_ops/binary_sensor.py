from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VectorOpsCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([VectorFailureSensor(hass.data[DOMAIN][entry.entry_id])])


class VectorFailureSensor(CoordinatorEntity[VectorOpsCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Update failure"
    _attr_unique_id = "vector_ops_update_failure"
    _attr_icon = "mdi:alert-circle-outline"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def is_on(self): return any(x.get("status") == "failed" for x in self.coordinator.data.get("queue", {}).get("items", []))

    @property
    def extra_state_attributes(self): return {"failed_items": [x for x in self.coordinator.data.get("queue", {}).get("items", []) if x.get("status") == "failed"]}
