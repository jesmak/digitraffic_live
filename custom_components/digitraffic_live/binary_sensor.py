"""A port's suspension: whether winter navigation has suspended the port now."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import ATTRIBUTION
from .coordinator import DigitrafficConfigEntry, PortCoordinator
from .ports import in_force
from .sensor import port_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DigitrafficConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    for subentry_id, coordinator in entry.runtime_data.coordinators.items():
        if isinstance(coordinator, PortCoordinator) and coordinator.port_config.winter_location:
            async_add_entities([PortSuspensionSensor(coordinator)], config_subentry_id=subentry_id)


class PortSuspensionSensor(CoordinatorEntity[PortCoordinator], BinarySensorEntity):
    """On while the port is suspended, such as in bad weather or an icebreaker's crew change."""

    _unrecorded_attributes = frozenset({"suspensions"})
    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_translation_key = "port_suspension"
    _attr_icon = "mdi:anchor"

    def __init__(self, coordinator: PortCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.subentry.subentry_id}_suspension"
        self._attr_device_info = port_device_info(coordinator)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.winter is not None

    # Home Assistant reads the state and the attributes only while the entity is available, so they have winter data.

    @property
    def is_on(self) -> bool:
        return in_force(self.coordinator.data.winter.suspensions, dt_util.utcnow()) is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        winter = self.coordinator.data.winter
        current = in_force(winter.suspensions, dt_util.utcnow())
        return {
            "reason": current.text if current else None,
            # Whether the port is closed to every operation.
            "port_closed": current.closed if current else None,
            "suspensions": [{**period.as_attribute("reason"), "port_closed": period.closed} for period in winter.suspensions],
        }
