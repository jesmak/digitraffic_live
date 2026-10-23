"""Update coordinators: one per config subentry.

A subentry is a map feed, a railway station's departures, a road weather station or a road weather camera.

Data that several feeds need (vessel register, icebreakers, passenger notices,
road station lists and details) lives in DigitrafficRuntimeData and is shared.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import DigitrafficClient, DigitrafficError
from .cache import DetailCache
from .const import (
    CONF_CAMERA,
    CONF_REFRESH_SECONDS,
    CONF_STATION,
    DEFAULT_REFRESH_SECONDS,
    DEFAULT_WEATHER_CAMERA_REFRESH_SECONDS,
    DEFAULT_WEATHER_STATION_REFRESH_SECONDS,
    DIRECTION_ARRIVALS,
    DIRECTION_DEPARTURES,
    DOMAIN,
    MIN_REFRESH_SECONDS,
    SUBENTRY_ROAD_CONDITIONS,
    SUBENTRY_ROAD_MAINTENANCE,
    SUBENTRY_ROAD_WEATHER_STATION,
    SUBENTRY_SHIPS,
    SUBENTRY_STATION_DEPARTURES,
    SUBENTRY_TRAFFIC_MESSAGES,
    SUBENTRY_TRAINS,
    SUBENTRY_WEATHER_CAMERA,
    SUBENTRY_WEATHER_CAMERAS,
    SUBENTRY_WEATHER_STATIONS,
)
from .geo import Area
from .maintenance import MaintenanceFeedConfig, build_maintenance_features, fetch_maintenance, stable_vehicle_ids, task_names
from .road_conditions import RoadConditionFeedConfig, build_road_condition_features, count_poor, section_index
from .ships import ShipFeedConfig, VesselRegister, build_ship_features, fetch_ship_positions
from .station_departures import (
    ARRIVED_LISTED,
    FETCH_FACTOR,
    PASSENGER_CATEGORIES,
    StationDeparturesConfig,
    build_arrivals,
    build_departures,
)
from .texts import Texts
from .traffic_messages import TrafficMessageFeedConfig, build_traffic_message_features, fetch_traffic_messages
from .trains import PassengerNotices, TrainFeedConfig, build_train_features, build_train_query
from .weather_cameras import (
    WeatherCameraFeedConfig,
    build_weather_camera_features,
    cameras_in_area,
    fetch_picture_times,
    picture_times,
    view_names,
    views_in_collection,
)
from .weather_stations import (
    WeatherStationFeedConfig,
    build_weather_station_features,
    fetch_sensor_values,
    stations_in_area,
)

_LOGGER = logging.getLogger(__name__)


class PeriodicValue[T]:
    """A value several feeds need, fetched at most every `interval_seconds`.

    A failed fetch keeps the previous value: missing icebreaker highlights or
    notices shouldn't make a whole feed unavailable. It is tried again after
    `retry_seconds`, so a value fetched once a day isn't missing for a day.
    """

    def __init__(
        self,
        name: str,
        interval_seconds: float,
        fetch: Callable[[], Awaitable[T]],
        initial: T,
        retry_seconds: float = 60,
    ) -> None:
        self._name = name
        self._interval = interval_seconds
        self._retry = min(retry_seconds, interval_seconds)
        self._fetch = fetch
        self._value = initial
        self._next_fetch: float | None = None
        self._lock = asyncio.Lock()
        self._failing = False
        self.loaded = False

    @property
    def name(self) -> str:
        return self._name

    async def get(self) -> T:
        async with self._lock:
            now = time.monotonic()
            if self._next_fetch is None or now >= self._next_fetch:
                try:
                    self._value = await self._fetch()
                    self._next_fetch = now + self._interval
                    self.loaded = True
                    if self._failing:
                        _LOGGER.info("Updating %s works again", self._name)
                        self._failing = False
                except DigitrafficError as err:
                    # Once per outage, so a lasting one shows in the log without filling it.
                    log = _LOGGER.debug if self._failing else _LOGGER.warning
                    log("Updating %s failed, using the previous value: %s", self._name, err)
                    self._failing = True
                    self._next_fetch = now + self._retry
        return self._value


@dataclass
class DigitrafficRuntimeData:
    client: DigitrafficClient
    texts: Texts
    vessel_register: VesselRegister
    icebreakers: PeriodicValue[set[int]]
    notices: PeriodicValue[PassengerNotices]
    maintenance_tasks: PeriodicValue[list[dict[str, Any]]]
    forecast_sections: PeriodicValue[dict[str, Any]]
    weather_station_list: PeriodicValue[dict[str, Any]]
    weather_station_details: DetailCache[str]
    camera_list: PeriodicValue[dict[str, Any]]
    camera_details: DetailCache[str]
    # Railway station names by short code, for where each departing train is heading.
    station_names: PeriodicValue[dict[str, str]]
    coordinators: dict[str, SubentryCoordinator[Any]] = field(default_factory=dict)


type DigitrafficConfigEntry = ConfigEntry[DigitrafficRuntimeData]


@dataclass(frozen=True)
class FeedData:
    features: list[dict[str, Any]]
    updated: datetime
    # The sensor's state; None counts the Point features.
    count: int | None = None


class SubentryCoordinator[T](DataUpdateCoordinator[T]):
    """Fetches the data of one config subentry."""

    config_entry: DigitrafficConfigEntry
    # Used when the subentry has no update interval of its own.
    default_refresh_seconds = DEFAULT_REFRESH_SECONDS

    def __init__(self, hass: HomeAssistant, entry: DigitrafficConfigEntry, subentry: ConfigSubentry) -> None:
        refresh_seconds = max(MIN_REFRESH_SECONDS, int(subentry.data.get(CONF_REFRESH_SECONDS, self.default_refresh_seconds)))
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} {subentry.title}",
            update_interval=timedelta(seconds=refresh_seconds),
        )
        self.subentry = subentry

    @property
    def runtime(self) -> DigitrafficRuntimeData:
        return self.config_entry.runtime_data


class FeedCoordinator(SubentryCoordinator[FeedData]):
    """Fetches one feed. Subclasses build the features."""

    @property
    def area(self) -> Area | None:
        return None

    async def _async_update_data(self) -> FeedData:
        try:
            features = await self._async_fetch_features()
        except DigitrafficError as err:
            raise UpdateFailed(str(err)) from err
        return FeedData(features=features, updated=dt_util.utcnow(), count=self.count(features))

    async def _async_fetch_features(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    def count(self, features: list[dict[str, Any]]) -> int | None:
        """The sensor's state, when it isn't the number of Point features."""
        return None

    async def shared[T](self, value: PeriodicValue[T]) -> T:
        """A shared list the feed can't do without; the feed is unavailable until it has been fetched."""
        result = await value.get()
        if not value.loaded:
            raise DigitrafficError(f"Digitraffic's {value.name} couldn't be loaded")
        return result


class ShipFeedCoordinator(FeedCoordinator):
    def __init__(self, hass: HomeAssistant, entry: DigitrafficConfigEntry, subentry: ConfigSubentry) -> None:
        super().__init__(hass, entry, subentry)
        self.feed_config = ShipFeedConfig.from_data(subentry.data)

    @property
    def area(self) -> Area | None:
        return self.feed_config.area

    async def _async_fetch_features(self) -> list[dict[str, Any]]:
        runtime = self.runtime
        now_ms = int(dt_util.utcnow().timestamp() * 1000)
        positions = await fetch_ship_positions(runtime.client, self.feed_config, now_ms)
        await runtime.vessel_register.ensure(runtime.client, (int(position["properties"]["mmsi"]) for position in positions))
        icebreakers = await runtime.icebreakers.get() if self.feed_config.icebreakers else set()
        return build_ship_features(positions, runtime.vessel_register, icebreakers, self.feed_config, runtime.texts)


class TrainFeedCoordinator(FeedCoordinator):
    def __init__(self, hass: HomeAssistant, entry: DigitrafficConfigEntry, subentry: ConfigSubentry) -> None:
        super().__init__(hass, entry, subentry)
        self.feed_config = TrainFeedConfig.from_data(subentry.data)
        # The filters come from the settings and don't change, so the query is built once.
        self._query = build_train_query(self.feed_config.route, self.feed_config.categories)

    @property
    def area(self) -> Area | None:
        return self.feed_config.area

    async def _async_fetch_features(self) -> list[dict[str, Any]]:
        runtime = self.runtime
        trains = await runtime.client.running_trains(self._query)
        notices = await runtime.notices.get()
        return build_train_features(trains, notices.trains, self.feed_config, runtime.texts, dt_util.utcnow())


class TrafficMessageFeedCoordinator(FeedCoordinator):
    def __init__(self, hass: HomeAssistant, entry: DigitrafficConfigEntry, subentry: ConfigSubentry) -> None:
        super().__init__(hass, entry, subentry)
        self.feed_config = TrafficMessageFeedConfig.from_data(subentry.data)

    @property
    def area(self) -> Area | None:
        return self.feed_config.area

    async def _async_fetch_features(self) -> list[dict[str, Any]]:
        now = dt_util.utcnow()
        situations = await fetch_traffic_messages(self.runtime.client, self.feed_config, now)
        return build_traffic_message_features(situations, self.runtime.texts, now)


class RoadMaintenanceFeedCoordinator(FeedCoordinator):
    def __init__(self, hass: HomeAssistant, entry: DigitrafficConfigEntry, subentry: ConfigSubentry) -> None:
        super().__init__(hass, entry, subentry)
        self.feed_config = MaintenanceFeedConfig.from_data(subentry.data)
        self._vehicle_ids: dict[Any, Any] = {}

    @property
    def area(self) -> Area | None:
        return self.feed_config.area

    async def _async_fetch_features(self) -> list[dict[str, Any]]:
        runtime = self.runtime
        vehicles, routes = await fetch_maintenance(runtime.client, self.feed_config, dt_util.utcnow())
        self._vehicle_ids = stable_vehicle_ids(vehicles, routes, self._vehicle_ids)
        # Task names are only labels: without them, the task ids are shown.
        names = task_names(await runtime.maintenance_tasks.get(), runtime.texts.language)
        shown = routes if self.feed_config.show_routes else []
        return build_maintenance_features(vehicles, shown, names, runtime.texts, self._vehicle_ids)


class RoadConditionFeedCoordinator(FeedCoordinator):
    def __init__(self, hass: HomeAssistant, entry: DigitrafficConfigEntry, subentry: ConfigSubentry) -> None:
        super().__init__(hass, entry, subentry)
        self.feed_config = RoadConditionFeedConfig.from_data(subentry.data)

    @property
    def area(self) -> Area | None:
        return self.feed_config.area

    async def _async_fetch_features(self) -> list[dict[str, Any]]:
        runtime = self.runtime
        sections = section_index(await self.shared(runtime.forecast_sections))
        forecasts = await runtime.client.forecasts(self.feed_config.area.bbox())
        return build_road_condition_features(forecasts, sections, self.feed_config, runtime.texts)

    def count(self, features: list[dict[str, Any]]) -> int | None:
        return count_poor(features)


class WeatherStationFeedCoordinator(FeedCoordinator):
    def __init__(self, hass: HomeAssistant, entry: DigitrafficConfigEntry, subentry: ConfigSubentry) -> None:
        super().__init__(hass, entry, subentry)
        self.feed_config = WeatherStationFeedConfig.from_data(subentry.data)

    @property
    def area(self) -> Area | None:
        return self.feed_config.area

    async def _async_fetch_features(self) -> list[dict[str, Any]]:
        runtime = self.runtime
        stations = stations_in_area(await self.shared(runtime.weather_station_list), self.feed_config.area)
        station_ids = [station.id for station in stations]
        await runtime.weather_station_details.ensure(station_ids)
        values = await fetch_sensor_values(runtime.client, station_ids)
        return build_weather_station_features(
            stations, runtime.weather_station_details, values, runtime.texts, self.feed_config.marker_value
        )


class WeatherCameraFeedCoordinator(FeedCoordinator):
    def __init__(self, hass: HomeAssistant, entry: DigitrafficConfigEntry, subentry: ConfigSubentry) -> None:
        super().__init__(hass, entry, subentry)
        self.feed_config = WeatherCameraFeedConfig.from_data(subentry.data)

    @property
    def area(self) -> Area | None:
        return self.feed_config.area

    async def _async_fetch_features(self) -> list[dict[str, Any]]:
        runtime = self.runtime
        cameras = cameras_in_area(await self.shared(runtime.camera_list), self.feed_config.area)
        camera_ids = [camera.id for camera in cameras]
        await runtime.camera_details.ensure(camera_ids)
        times = await fetch_picture_times(runtime.client, camera_ids)
        return build_weather_camera_features(cameras, runtime.camera_details, times, runtime.texts.language)


@dataclass(frozen=True)
class StationDepartures:
    station: str
    name: str
    # Departures in the departures format, soonest first, and arrivals in the same shape, by direction.
    trains: dict[str, list[dict[str, Any]]]
    # Station-wide passenger notices in force, such as track works.
    notices: list[str]

    def next_train(self, direction: str) -> dict[str, Any] | None:
        """The first that isn't cancelled and, for arrivals, hasn't come in."""
        return next((train for train in self.trains.get(direction, []) if not train.get("cancelled") and not train.get("arrived")), None)


class StationDeparturesCoordinator(SubentryCoordinator[StationDepartures]):
    """The next passenger trains to leave or reach one railway station, both directions in one request."""

    def __init__(self, hass: HomeAssistant, entry: DigitrafficConfigEntry, subentry: ConfigSubentry) -> None:
        super().__init__(hass, entry, subentry)
        self.departures_config = StationDeparturesConfig.from_data(subentry.data)

    async def _async_update_data(self) -> StationDepartures:
        runtime = self.runtime
        config = self.departures_config
        names = await runtime.station_names.get()
        if not runtime.station_names.loaded:
            raise UpdateFailed("Digitraffic's station list couldn't be loaded")
        try:
            # A station's own list is mostly commuter trains at a big one: Helsinki's next twenty leave within a quarter
            # of an hour, and a train to the "stops at" station wouldn't be among them.
            # "Stops at" is for departures only, which the flow sees to.
            if config.stops_at:
                trains = await runtime.client.trains_between(config.station, config.stops_at, config.fetch_count)
            else:
                arrivals = DIRECTION_ARRIVALS in config.directions
                trains = await runtime.client.station_trains(
                    config.station,
                    PASSENGER_CATEGORIES,
                    departing=config.fetch_count if DIRECTION_DEPARTURES in config.directions else 0,
                    arriving=config.fetch_count if arrivals else 0,
                    arrived=ARRIVED_LISTED * FETCH_FACTOR if arrivals else 0,
                )
        except DigitrafficError as err:
            raise UpdateFailed(str(err)) from err
        # Notices only add to the departures: without them, the departures are shown all the same.
        notices = await runtime.notices.get()
        built: dict[str, list[dict[str, Any]]] = {}
        if DIRECTION_DEPARTURES in config.directions:
            built[DIRECTION_DEPARTURES] = build_departures(trains, config, names, notices.trains, runtime.texts, dt_util.utcnow())
        if DIRECTION_ARRIVALS in config.directions:
            built[DIRECTION_ARRIVALS] = build_arrivals(trains, config, names, notices.trains, runtime.texts, dt_util.utcnow())
        return StationDepartures(
            config.station,
            names.get(config.station, config.station),
            built,
            notices.for_station(config.station, dt_util.utcnow()),
        )


class WeatherStationCoordinator(SubentryCoordinator[dict[str, Mapping[str, Any]]]):
    """The latest sensor values of one road weather station, by sensor name."""

    default_refresh_seconds = DEFAULT_WEATHER_STATION_REFRESH_SECONDS

    def __init__(self, hass: HomeAssistant, entry: DigitrafficConfigEntry, subentry: ConfigSubentry) -> None:
        super().__init__(hass, entry, subentry)
        self.station_id = str(subentry.data[CONF_STATION])

    async def _async_update_data(self) -> dict[str, Mapping[str, Any]]:
        try:
            data = await self.runtime.client.weather_station_data(self.station_id)
        except DigitrafficError as err:
            raise UpdateFailed(str(err)) from err
        return {str(value.get("name")): value for value in data.get("sensorValues") or []}


@dataclass(frozen=True)
class CameraData:
    # Preset ids of the views being photographed, and the names of those that have one, such as "Imatralle".
    views: tuple[str, ...]
    view_names: dict[str, str]
    # When each view was last photographed, by preset id.
    picture_times: dict[str, str]


class WeatherCameraCoordinator(SubentryCoordinator[CameraData]):
    """The views of one road weather camera and when each was last photographed."""

    default_refresh_seconds = DEFAULT_WEATHER_CAMERA_REFRESH_SECONDS

    def __init__(self, hass: HomeAssistant, entry: DigitrafficConfigEntry, subentry: ConfigSubentry) -> None:
        super().__init__(hass, entry, subentry)
        self.camera_id = str(subentry.data[CONF_CAMERA])

    async def _async_update_data(self) -> CameraData:
        runtime = self.runtime
        await runtime.camera_details.ensure([self.camera_id])
        details = runtime.camera_details.get(self.camera_id)
        if details is None:
            raise UpdateFailed(f"The details of weather camera {self.camera_id} couldn't be fetched")
        try:
            data = await runtime.client.weathercam_station_data(self.camera_id)
        except DigitrafficError as err:
            raise UpdateFailed(str(err)) from err
        return CameraData(views_in_collection(details), view_names(details), picture_times(data))


COORDINATORS: dict[str, type[SubentryCoordinator[Any]]] = {
    SUBENTRY_SHIPS: ShipFeedCoordinator,
    SUBENTRY_TRAINS: TrainFeedCoordinator,
    SUBENTRY_TRAFFIC_MESSAGES: TrafficMessageFeedCoordinator,
    SUBENTRY_ROAD_MAINTENANCE: RoadMaintenanceFeedCoordinator,
    SUBENTRY_ROAD_CONDITIONS: RoadConditionFeedCoordinator,
    SUBENTRY_WEATHER_STATIONS: WeatherStationFeedCoordinator,
    SUBENTRY_WEATHER_CAMERAS: WeatherCameraFeedCoordinator,
    SUBENTRY_STATION_DEPARTURES: StationDeparturesCoordinator,
    SUBENTRY_ROAD_WEATHER_STATION: WeatherStationCoordinator,
    SUBENTRY_WEATHER_CAMERA: WeatherCameraCoordinator,
}
