from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VectorOpsCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VectorUpdatesSensor(coordinator), VectorReviewSensor(coordinator), VectorQueueSensor(coordinator), VectorHealthSensor(coordinator), VectorInfrastructureSensor(coordinator), VectorBackupSensor(coordinator), VectorIncidentsSensor(coordinator), VectorWeatherSensor(coordinator)])


class VectorSensor(CoordinatorEntity[VectorOpsCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: VectorOpsCoordinator, key: str, name: str, icon: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"vector_ops_{key}"
        self._attr_device_info = {"identifiers": {(DOMAIN, "vector_ops")}, "name": "Vector Ops", "manufacturer": "Vector", "model": "Queue service", "configuration_url": coordinator.api.base_url}


class VectorUpdatesSensor(VectorSensor):
    def __init__(self, coordinator): super().__init__(coordinator, "updates_available", "Updates available", "mdi:update")

    @property
    def native_value(self): return self.coordinator.data.get("data", {}).get("count", 0)

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data.get("data", {})
        items = [dict(x, kind="container") for x in data.get("containers", [])]
        items += [dict(x, id="ha:" + x.get("entity_id", ""), kind="homeassistant", approved=True, service_key=x.get("service_key", "homeassistant")) for x in data.get("homeassistant", {}).get("items", [])]
        return {"items": items, "generated_at": data.get("generated_at"), "scanning": self.coordinator.data.get("scanning", False), "backend_url": self.coordinator.api.base_url}


class VectorReviewSensor(VectorSensor):
    def __init__(self, coordinator): super().__init__(coordinator, "review_required", "Review required", "mdi:clipboard-alert-outline")

    @property
    def native_value(self): return sum(not x.get("approved", False) for x in self.coordinator.data.get("data", {}).get("containers", []))


class VectorQueueSensor(VectorSensor):
    def __init__(self, coordinator): super().__init__(coordinator, "queue", "Queue", "mdi:playlist-play")

    @property
    def native_value(self):
        q = self.coordinator.data.get("queue", {}); items = q.get("items", [])
        if q.get("running") or any(x.get("status") == "running" for x in items): return "running"
        if any(x.get("status") == "failed" for x in items): return "failed"
        if any(x.get("status") == "waiting" for x in items): return "staged"
        if any(x.get("status") == "pending" for x in items): return "pending"
        return "complete" if items else "empty"

    @property
    def extra_state_attributes(self):
        q = self.coordinator.data.get("queue", {})
        return {"items": q.get("items", []), "running": q.get("running", False), "paused": q.get("paused", False), "interval_minutes": q.get("interval_minutes", 0), "last": q.get("last")}


class VectorHealthSensor(VectorSensor):
    def __init__(self, coordinator): super().__init__(coordinator, "service_health", "Service health", "mdi:heart-pulse")

    @property
    def native_value(self): return self.coordinator.data.get("overview", {}).get("summary", {}).get("status", "unknown")

    @property
    def extra_state_attributes(self):
        overview = self.coordinator.data.get("overview", {}); summary = overview.get("summary", {})
        return {"services_ok": summary.get("services_ok", 0), "services_total": summary.get("services_total", 0), "problems": summary.get("problems", 0), "routes": overview.get("routes", [])}


class VectorInfrastructureSensor(VectorSensor):
    def __init__(self, coordinator): super().__init__(coordinator, "infrastructure", "Infrastructure", "mdi:server-network")

    @property
    def native_value(self): return "healthy" if self.coordinator.data.get("overview", {}).get("infrastructure_uptime", {}).get("ok") else "attention"

    @property
    def extra_state_attributes(self): return {"items": self.coordinator.data.get("overview", {}).get("infrastructure_uptime", {}).get("items", [])}


class VectorBackupSensor(VectorSensor):
    def __init__(self, coordinator): super().__init__(coordinator, "backup", "Backup", "mdi:backup-restore")

    @property
    def native_value(self): return "healthy" if self.coordinator.data.get("overview", {}).get("backup", {}).get("ok") else "attention"

    @property
    def extra_state_attributes(self): return self.coordinator.data.get("overview", {}).get("backup", {})


class VectorIncidentsSensor(VectorSensor):
    def __init__(self, coordinator): super().__init__(coordinator, "incidents", "Incidents", "mdi:alert-decagram-outline")

    @property
    def native_value(self): return len(self.coordinator.data.get("overview", {}).get("incidents", []))

    @property
    def extra_state_attributes(self): return {"items": self.coordinator.data.get("overview", {}).get("incidents", [])}


class VectorWeatherSensor(VectorSensor):
    def __init__(self, coordinator): super().__init__(coordinator, "weather", "Weather", "mdi:weather-partly-cloudy")

    @property
    def native_value(self): return self.coordinator.data.get("overview", {}).get("weather", {}).get("summary", "unknown")

    @property
    def extra_state_attributes(self):
        weather = self.coordinator.data.get("overview", {}).get("weather", {})
        return {"temperature": weather.get("temperature"), "feels_like": weather.get("feels"), "wind": weather.get("wind"), "precipitation": weather.get("precipitation"), "forecast": weather.get("days", [])}
