"""Map feed sensors, one per feed, station departure sensors, and the sensors of road weather stations.

A feed sensor's state is the number of items; the items are in the `geojson`
attribute, in the Map Feed format (docs/map-feed-format.md in map-feed-card).
A station departure sensor's state is the time of the next train that isn't cancelled;
the departures are in the `departures` attribute, in the departures format
(docs/departures-format.md in departures-card).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import MATCH_ALL, UnitOfLength, UnitOfSpeed, UnitOfTemperature, UnitOfVolumetricFlux
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    ATTRIBUTION,
    DEPARTURES_VERSION,
    DIRECTION_ARRIVALS,
    DIRECTION_BOTH,
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
from .coordinator import (
    DigitrafficConfigEntry,
    FeedCoordinator,
    StationDeparturesCoordinator,
    WeatherStationCoordinator,
)
from .feed import feature_collection
from .weather_stations import (
    GRIP_CONDITIONS,
    PRECIPITATION_STATES,
    PRECIPITATION_TYPES,
    SURFACE_STATES,
    WARNING_STATES,
    station_readings,
)

ICONS = {
    SUBENTRY_SHIPS: "mdi:ferry",
    SUBENTRY_TRAINS: "mdi:train",
    SUBENTRY_TRAFFIC_MESSAGES: "mdi:alert",
    SUBENTRY_ROAD_MAINTENANCE: "mdi:truck-snowflake",
    SUBENTRY_ROAD_CONDITIONS: "mdi:road-variant",
    SUBENTRY_WEATHER_STATIONS: "mdi:thermometer",
    SUBENTRY_WEATHER_CAMERAS: "mdi:cctv",
}


# What each feed is about, as the map feed format's families; the card offers each only the options that fit it.
FEED_TYPES = {
    SUBENTRY_SHIPS: "ship",
    SUBENTRY_TRAINS: "train",
    SUBENTRY_TRAFFIC_MESSAGES: "road",
    SUBENTRY_ROAD_MAINTENANCE: "road",
    SUBENTRY_ROAD_CONDITIONS: "road",
    SUBENTRY_WEATHER_STATIONS: "road",
    SUBENTRY_WEATHER_CAMERAS: "road",
}


# Sensors every road weather station gets. The keys are those of station_readings().
STATION_SENSORS = (
    SensorEntityDescription(
        key="road_temperature",
        translation_key="road_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    SensorEntityDescription(
        key="air_temperature",
        translation_key="air_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    SensorEntityDescription(
        key="road_surface",
        translation_key="road_surface",
        device_class=SensorDeviceClass.ENUM,
        options=list(SURFACE_STATES.values()),
        icon="mdi:road-variant",
    ),
    SensorEntityDescription(
        key="grip",
        translation_key="grip",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="µ",
        suggested_display_precision=2,
        icon="mdi:car-traction-control",
    ),
    SensorEntityDescription(
        key="grip_condition",
        translation_key="grip_condition",
        device_class=SensorDeviceClass.ENUM,
        options=[condition for _, condition in GRIP_CONDITIONS],
        icon="mdi:car-traction-control",
    ),
    SensorEntityDescription(
        key="road_warning",
        translation_key="road_warning",
        device_class=SensorDeviceClass.ENUM,
        options=list(WARNING_STATES.values()),
        icon="mdi:alert",
    ),
    SensorEntityDescription(
        key="wind_speed",
        translation_key="wind_speed",
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        # Home Assistant would convert to km/h; Finnish weather services give wind in m/s.
        suggested_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="wind_gusts",
        translation_key="wind_gusts",
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        suggested_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="precipitation",
        translation_key="precipitation",
        device_class=SensorDeviceClass.ENUM,
        options=list(PRECIPITATION_STATES.values()),
        icon="mdi:weather-pouring",
    ),
    SensorEntityDescription(
        key="precipitation_type",
        translation_key="precipitation_type",
        device_class=SensorDeviceClass.ENUM,
        options=list(PRECIPITATION_TYPES.values()),
        icon="mdi:weather-snowy-rainy",
    ),
    SensorEntityDescription(
        key="rain_intensity",
        translation_key="rain_intensity",
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="visibility",
        translation_key="visibility",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        suggested_display_precision=1,
        icon="mdi:eye",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DigitrafficConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    for subentry_id, coordinator in entry.runtime_data.coordinators.items():
        if isinstance(coordinator, FeedCoordinator):
            async_add_entities([MapFeedSensor(coordinator)], config_subentry_id=subentry_id)
        elif isinstance(coordinator, StationDeparturesCoordinator):
            async_add_entities(
                [StationDeparturesSensor(coordinator, direction) for direction in coordinator.departures_config.directions],
                config_subentry_id=subentry_id,
            )
        elif isinstance(coordinator, WeatherStationCoordinator):
            async_add_entities(
                [StationSensor(coordinator, description) for description in STATION_SENSORS],
                config_subentry_id=subentry_id,
            )


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
        subentry_type = self.coordinator.subentry.subentry_type
        if feed_type := FEED_TYPES.get(subentry_type):
            attributes["feed_type"] = feed_type
        if subentry_type == SUBENTRY_TRAINS:
            texts = self.coordinator.runtime.texts
            attributes["list"] = {
                "sort": [
                    {"key": "delay", "label": texts("sort_delay"), "property": "delay_minutes", "order": "desc"},
                    {"key": "number", "label": texts("sort_number"), "property": "badge"},
                ],
                "default": "delay",
                "count": texts("trains_count"),
            }
        if area := self.coordinator.area:
            attributes["area"] = area.as_attribute()
        if data := self.coordinator.data:
            attributes["updated"] = data.updated.isoformat(timespec="seconds")
            attributes["geojson"] = feature_collection(data.features)
        return attributes


class StationDeparturesSensor(CoordinatorEntity[StationDeparturesCoordinator], SensorEntity):
    """The time of a station's next train to leave that isn't cancelled, or to arrive that hasn't come in, with the live
    estimate when there is one."""

    # The departures change on every update; the next departure time is history enough.
    _unrecorded_attributes = frozenset({"departures", "notices"})
    _attr_attribution = ATTRIBUTION
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_has_entity_name = True

    def __init__(self, coordinator: StationDeparturesCoordinator, direction: str) -> None:
        super().__init__(coordinator)
        subentry = coordinator.subentry
        self.direction = direction
        if direction == DIRECTION_ARRIVALS:
            # "Lappeenranta saapuvat"; the station's name alone is its departures'.
            self._attr_unique_id = f"{subentry.subentry_id}_arrivals"
            self._attr_translation_key = "station_arrivals"
            self._attr_icon = "mdi:train"
        else:
            # The departures' unique id is the subentry's, as it was before arrivals.
            self._attr_unique_id = subentry.subentry_id
            self._attr_name = None
            self._attr_icon = "mdi:train-variant"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, subentry.subentry_id)},
            name=subentry.title,
            manufacturer="Fintraffic",
            model_id=coordinator.departures_config.station,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> datetime | None:
        data = self.coordinator.data
        train = data.next_train(self.direction) if data else None
        return dt_util.parse_datetime(train["estimated"]) if train else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data
        if data is None:
            return {}
        attributes: dict[str, Any] = {
            "departures_version": DEPARTURES_VERSION,
            "stop_id": data.station,
            "stop_name": data.name,
        }
        # Departures say so only next to their station's arrivals, so a station board of departures alone reads as before.
        if self.direction == DIRECTION_ARRIVALS or self.coordinator.departures_config.direction == DIRECTION_BOTH:
            attributes["direction"] = self.direction
        if data.notices:
            attributes["notices"] = data.notices
        attributes["departures"] = data.trains.get(self.direction, [])
        return attributes


class StationSensor(CoordinatorEntity[WeatherStationCoordinator], SensorEntity):
    """One value of a road weather station. Values the station doesn't measure stay unknown."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(self, coordinator: WeatherStationCoordinator, description: SensorEntityDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        subentry = coordinator.subentry
        self._attr_unique_id = f"{subentry.subentry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, subentry.subentry_id)},
            name=subentry.title,
            manufacturer="Fintraffic",
            model_id=coordinator.station_id,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> float | str | None:
        return station_readings(self.coordinator.data or {}).get(self.entity_description.key)
