"""Map feed sensors: one per feed.

The state is the number of items; the items are in the `geojson` attribute, in
the Map Feed format (docs/map-feed-format.md in ha-map-card-plugin-map-feed).
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTRIBUTION,
    DOMAIN,
    MAP_FEED_VERSION,
    SUBENTRY_ROAD_CONDITIONS,
    SUBENTRY_ROAD_MAINTENANCE,
    SUBENTRY_SHIPS,
    SUBENTRY_TRAFFIC_MESSAGES,
    SUBENTRY_TRAINS,
    SUBENTRY_WEATHER_CAMERAS,
    SUBENTRY_WEATHER_STATIONS,
)
from .coordinator import DigitrafficConfigEntry, FeedCoordinator
from .feed import feature_collection

ICONS = {
    SUBENTRY_SHIPS: "mdi:ferry",
    SUBENTRY_TRAINS: "mdi:train",
    SUBENTRY_TRAFFIC_MESSAGES: "mdi:alert",
    SUBENTRY_ROAD_MAINTENANCE: "mdi:snowplow",
    SUBENTRY_ROAD_CONDITIONS: "mdi:road-variant",
    SUBENTRY_WEATHER_STATIONS: "mdi:thermometer",
    SUBENTRY_WEATHER_CAMERAS: "mdi:cctv",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DigitrafficConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    for subentry_id, coordinator in entry.runtime_data.coordinators.items():
        async_add_entities([MapFeedSensor(coordinator)], config_subentry_id=subentry_id)


class MapFeedSensor(CoordinatorEntity[FeedCoordinator], SensorEntity):
    # The feed changes every minute and can be tens of kilobytes: only the count goes to the database.
    _unrecorded_attributes = frozenset({MATCH_ALL})
    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, coordinator: FeedCoordinator) -> None:
        super().__init__(coordinator)
        subentry = coordinator.subentry
        self._attr_unique_id = subentry.subentry_id
        self._attr_icon = ICONS.get(subentry.subentry_type)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, subentry.subentry_id)},
            name=subentry.title,
            manufacturer="Fintraffic",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> int | None:
        data = self.coordinator.data
        if data is None:
            return None
        if data.count is not None:
            return data.count
        return sum(1 for feature in data.features if feature["geometry"]["type"] == "Point")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attributes: dict[str, Any] = {"map_feed_version": MAP_FEED_VERSION}
        if area := self.coordinator.area:
            attributes["area"] = area.as_attribute()
        if data := self.coordinator.data:
            attributes["updated"] = data.updated.isoformat(timespec="seconds")
            attributes["geojson"] = feature_collection(data.features)
        return attributes
