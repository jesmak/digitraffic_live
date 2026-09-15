"""Config flow.

The config entry holds only the language. Each feed is a config subentry
(ships, trains, traffic messages, road maintenance, road conditions, weather
stations or weather cameras), added and changed from the integration page.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigEntryState,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentry,
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    LocationSelector,
    LocationSelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)

from .api import DigitrafficError
from .cache import details_name
from .const import (
    CONF_AREA,
    CONF_CAMERA,
    CONF_CATEGORIES,
    CONF_FORECAST,
    CONF_ICEBREAKERS,
    CONF_INCLUDE_MOORED,
    CONF_LANGUAGE,
    CONF_MARKER_VALUE,
    CONF_MAX_AGE_MINUTES,
    CONF_MESSAGE_TYPES,
    CONF_ONLY_POOR,
    CONF_REFRESH_SECONDS,
    CONF_ROUTE,
    CONF_ROUTE_HOURS,
    CONF_SHIP_TYPES,
    CONF_SHOW_ROUTES,
    CONF_STATION,
    CONF_TASKS,
    CONF_UPCOMING_DAYS,
    CONF_USE_AREA,
    DEFAULT_MAINTENANCE_MAX_AGE_MINUTES,
    DEFAULT_REFRESH_SECONDS,
    DEFAULT_ROAD_CONDITION_REFRESH_SECONDS,
    DEFAULT_ROUTE_HOURS,
    DEFAULT_SHIP_MAX_AGE_MINUTES,
    DEFAULT_TRAFFIC_MESSAGE_REFRESH_SECONDS,
    DEFAULT_TRAIN_MAX_AGE_MINUTES,
    DEFAULT_UPCOMING_DAYS,
    DEFAULT_WEATHER_CAMERA_REFRESH_SECONDS,
    DEFAULT_WEATHER_STATION_REFRESH_SECONDS,
    DOMAIN,
    LANGUAGES,
    MIN_REFRESH_SECONDS,
    SUBENTRY_ROAD_CONDITIONS,
    SUBENTRY_ROAD_MAINTENANCE,
    SUBENTRY_ROAD_WEATHER_STATION,
    SUBENTRY_SHIPS,
    SUBENTRY_TRAFFIC_MESSAGES,
    SUBENTRY_TRAINS,
    SUBENTRY_WEATHER_CAMERA,
    SUBENTRY_WEATHER_CAMERAS,
    SUBENTRY_WEATHER_STATIONS,
)
from .maintenance import MAINTENANCE_TASKS, MAX_ROUTE_HOURS
from .road_conditions import FORECAST_TIMES
from .ships import SHIP_TYPES
from .traffic_messages import MESSAGE_TYPES
from .trains import TRAIN_CATEGORIES, station_name
from .weather_cameras import camera_options
from .weather_stations import DEFAULT_MARKER_VALUE, MARKER_VALUES, station_options

DEFAULT_SHIP_RADIUS_M = 15_000
DEFAULT_TRAIN_RADIUS_M = 30_000
DEFAULT_ROAD_RADIUS_M = 30_000
DEFAULT_ROAD_CONDITION_RADIUS_M = 50_000

MAX_AGE_SELECTOR = NumberSelector(
    NumberSelectorConfig(min=1, max=240, step=1, unit_of_measurement="min", mode=NumberSelectorMode.BOX)
)
REFRESH_SELECTOR = NumberSelector(
    NumberSelectorConfig(
        min=MIN_REFRESH_SECONDS, max=3600, step=1, unit_of_measurement="s", mode=NumberSelectorMode.BOX
    )
)


def language_schema(default: str) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_LANGUAGE, default=default): SelectSelector(
                SelectSelectorConfig(options=LANGUAGES, translation_key=CONF_LANGUAGE, mode=SelectSelectorMode.DROPDOWN)
            )
        }
    )


class DigitrafficLiveConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="Digitraffic", data=user_input)
        language = self.hass.config.language[:2]
        default = language if language in LANGUAGES else "en"
        return self.async_show_form(step_id="user", data_schema=language_schema(default))

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            # The update listener in __init__.py reloads the entry.
            self.hass.config_entries.async_update_entry(entry, data={**entry.data, **user_input})
            return self.async_abort(reason="reconfigure_successful")
        return self.async_show_form(step_id="reconfigure", data_schema=language_schema(entry.data[CONF_LANGUAGE]))

    @classmethod
    @callback
    def async_get_supported_subentry_types(cls, config_entry: ConfigEntry) -> dict[str, type[ConfigSubentryFlow]]:
        return {
            SUBENTRY_SHIPS: ShipFeedFlow,
            SUBENTRY_TRAINS: TrainFeedFlow,
            SUBENTRY_TRAFFIC_MESSAGES: TrafficMessageFeedFlow,
            SUBENTRY_ROAD_MAINTENANCE: RoadMaintenanceFeedFlow,
            SUBENTRY_ROAD_CONDITIONS: RoadConditionFeedFlow,
            SUBENTRY_WEATHER_STATIONS: WeatherStationFeedFlow,
            SUBENTRY_WEATHER_CAMERAS: WeatherCameraFeedFlow,
            SUBENTRY_ROAD_WEATHER_STATION: RoadWeatherStationFlow,
            SUBENTRY_WEATHER_CAMERA: WeatherCameraFlow,
        }


class FeedFlow(ConfigSubentryFlow):
    """Adding (step "user") and changing (step "reconfigure") one feed with a single form."""

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        return await self._async_step_feed("user", user_input, None)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        return await self._async_step_feed("reconfigure", user_input, self._get_reconfigure_subentry())

    async def _async_step_feed(
        self, step_id: str, user_input: dict[str, Any] | None, current: ConfigSubentry | None
    ) -> SubentryFlowResult:
        schema = await self.async_schema()
        if isinstance(schema, dict):  # an abort result
            return schema

        errors: dict[str, str] = {}
        if user_input is not None:
            data = dict(user_input)
            title = data.pop(CONF_NAME).strip()
            errors = self.validate(data)
            if not errors:
                data = self.clean(data)
                if current is None:
                    return self.async_create_entry(title=title, data=data)
                return self.async_update_and_abort(self._get_entry(), current, title=title, data=data)

        if user_input is not None:
            values = user_input
        elif current is not None:
            # Defaults fill in settings added after the feed was created.
            values = {**self.defaults(), CONF_NAME: current.title, **current.data}
        else:
            values = self.defaults()
        return self.async_show_form(
            step_id=step_id,
            data_schema=self.add_suggested_values_to_schema(schema, values),
            errors=errors,
        )

    async def async_schema(self) -> vol.Schema | SubentryFlowResult:
        raise NotImplementedError

    def defaults(self) -> dict[str, Any]:
        raise NotImplementedError

    def validate(self, data: dict[str, Any]) -> dict[str, str]:
        return {}

    def clean(self, data: dict[str, Any]) -> dict[str, Any]:
        """Normalises submitted values before they are stored."""
        for key in (CONF_MAX_AGE_MINUTES, CONF_REFRESH_SECONDS, CONF_UPCOMING_DAYS, CONF_ROUTE_HOURS):
            if key in data:
                data[key] = int(data[key])
        return data

    def home_area(self, radius_m: int) -> dict[str, float]:
        return {"latitude": self.hass.config.latitude, "longitude": self.hass.config.longitude, "radius": radius_m}


class ShipFeedFlow(FeedFlow):
    async def async_schema(self) -> vol.Schema:
        return vol.Schema(
            {
                vol.Required(CONF_NAME): TextSelector(),
                vol.Required(CONF_AREA): LocationSelector(LocationSelectorConfig(radius=True, icon="mdi:ferry")),
                vol.Optional(CONF_SHIP_TYPES): SelectSelector(
                    SelectSelectorConfig(options=list(SHIP_TYPES), multiple=True, translation_key=CONF_SHIP_TYPES)
                ),
                vol.Required(CONF_INCLUDE_MOORED): BooleanSelector(),
                vol.Required(CONF_ICEBREAKERS): BooleanSelector(),
                vol.Required(CONF_MAX_AGE_MINUTES): MAX_AGE_SELECTOR,
                vol.Required(CONF_REFRESH_SECONDS): REFRESH_SELECTOR,
            }
        )

    def defaults(self) -> dict[str, Any]:
        return {
            CONF_AREA: self.home_area(DEFAULT_SHIP_RADIUS_M),
            CONF_INCLUDE_MOORED: True,
            CONF_ICEBREAKERS: False,
            CONF_MAX_AGE_MINUTES: DEFAULT_SHIP_MAX_AGE_MINUTES,
            CONF_REFRESH_SECONDS: DEFAULT_REFRESH_SECONDS,
        }

    def validate(self, data: dict[str, Any]) -> dict[str, str]:
        if not data[CONF_AREA].get("radius"):
            return {CONF_AREA: "area_radius"}
        return {}


class TrainFeedFlow(FeedFlow):
    _stations: list[SelectOptionDict] | None = None

    async def async_schema(self) -> vol.Schema | SubentryFlowResult:
        entry = self._get_entry()
        if entry.state is not ConfigEntryState.LOADED:
            return self.async_abort(reason="entry_not_loaded")
        if self._stations is None:
            try:
                stations = await entry.runtime_data.client.stations()
            except DigitrafficError:
                return self.async_abort(reason="cannot_connect")
            self._stations = sorted(
                (
                    SelectOptionDict(
                        value=station["stationShortCode"],
                        label=f"{station_name(station['stationName'])} ({station['stationShortCode']})",
                    )
                    for station in stations
                    if station.get("passengerTraffic")
                ),
                key=lambda option: option["label"],
            )

        return vol.Schema(
            {
                vol.Required(CONF_NAME): TextSelector(),
                vol.Optional(CONF_ROUTE): SelectSelector(
                    SelectSelectorConfig(options=self._stations, multiple=True, mode=SelectSelectorMode.DROPDOWN)
                ),
                vol.Optional(CONF_CATEGORIES): SelectSelector(
                    SelectSelectorConfig(options=list(TRAIN_CATEGORIES), multiple=True, translation_key=CONF_CATEGORIES)
                ),
                vol.Required(CONF_USE_AREA): BooleanSelector(),
                vol.Optional(CONF_AREA): LocationSelector(LocationSelectorConfig(radius=True, icon="mdi:train")),
                vol.Required(CONF_MAX_AGE_MINUTES): MAX_AGE_SELECTOR,
                vol.Required(CONF_REFRESH_SECONDS): REFRESH_SELECTOR,
            }
        )

    def defaults(self) -> dict[str, Any]:
        return {
            CONF_USE_AREA: False,
            CONF_AREA: self.home_area(DEFAULT_TRAIN_RADIUS_M),
            CONF_MAX_AGE_MINUTES: DEFAULT_TRAIN_MAX_AGE_MINUTES,
            CONF_REFRESH_SECONDS: DEFAULT_REFRESH_SECONDS,
        }

    def validate(self, data: dict[str, Any]) -> dict[str, str]:
        route = data.get(CONF_ROUTE) or []
        if len(route) == 1:
            return {CONF_ROUTE: "route_too_short"}
        if data[CONF_USE_AREA]:
            area = data.get(CONF_AREA) or {}
            if not area.get("radius"):
                return {CONF_AREA: "area_radius"}
        elif not route:
            return {"base": "route_or_area"}
        return {}

    def clean(self, data: dict[str, Any]) -> dict[str, Any]:
        data = super().clean(data)
        if not data[CONF_USE_AREA]:
            # Without the area enabled the feed covers all of Finland; don't keep a stale circle around.
            data.pop(CONF_AREA, None)
        return data


class AreaFeedFlow(FeedFlow):
    """A feed of things inside a circle picked on a map."""

    def validate(self, data: dict[str, Any]) -> dict[str, str]:
        if not data[CONF_AREA].get("radius"):
            return {CONF_AREA: "area_radius"}
        return {}


class TrafficMessageFeedFlow(AreaFeedFlow):
    async def async_schema(self) -> vol.Schema:
        return vol.Schema(
            {
                vol.Required(CONF_NAME): TextSelector(),
                vol.Required(CONF_AREA): LocationSelector(LocationSelectorConfig(radius=True, icon="mdi:alert")),
                vol.Optional(CONF_MESSAGE_TYPES): SelectSelector(
                    SelectSelectorConfig(options=list(MESSAGE_TYPES), multiple=True, translation_key=CONF_MESSAGE_TYPES)
                ),
                vol.Required(CONF_UPCOMING_DAYS): NumberSelector(
                    NumberSelectorConfig(min=0, max=90, step=1, unit_of_measurement="d", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(CONF_REFRESH_SECONDS): REFRESH_SELECTOR,
            }
        )

    def defaults(self) -> dict[str, Any]:
        return {
            CONF_AREA: self.home_area(DEFAULT_ROAD_RADIUS_M),
            CONF_UPCOMING_DAYS: DEFAULT_UPCOMING_DAYS,
            CONF_REFRESH_SECONDS: DEFAULT_TRAFFIC_MESSAGE_REFRESH_SECONDS,
        }


class RoadMaintenanceFeedFlow(AreaFeedFlow):
    async def async_schema(self) -> vol.Schema:
        return vol.Schema(
            {
                vol.Required(CONF_NAME): TextSelector(),
                vol.Required(CONF_AREA): LocationSelector(LocationSelectorConfig(radius=True, icon="mdi:snowplow")),
                vol.Optional(CONF_TASKS): SelectSelector(
                    SelectSelectorConfig(
                        options=[task.lower() for task in MAINTENANCE_TASKS],
                        multiple=True,
                        translation_key=CONF_TASKS,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(CONF_MAX_AGE_MINUTES): MAX_AGE_SELECTOR,
                vol.Required(CONF_SHOW_ROUTES): BooleanSelector(),
                vol.Required(CONF_ROUTE_HOURS): NumberSelector(
                    NumberSelectorConfig(
                        min=1, max=MAX_ROUTE_HOURS, step=1, unit_of_measurement="h", mode=NumberSelectorMode.BOX
                    )
                ),
                vol.Required(CONF_REFRESH_SECONDS): REFRESH_SELECTOR,
            }
        )

    def defaults(self) -> dict[str, Any]:
        return {
            CONF_AREA: self.home_area(DEFAULT_ROAD_RADIUS_M),
            CONF_MAX_AGE_MINUTES: DEFAULT_MAINTENANCE_MAX_AGE_MINUTES,
            CONF_SHOW_ROUTES: True,
            CONF_ROUTE_HOURS: DEFAULT_ROUTE_HOURS,
            CONF_REFRESH_SECONDS: DEFAULT_REFRESH_SECONDS,
        }


class RoadConditionFeedFlow(AreaFeedFlow):
    async def async_schema(self) -> vol.Schema:
        return vol.Schema(
            {
                vol.Required(CONF_NAME): TextSelector(),
                vol.Required(CONF_AREA): LocationSelector(LocationSelectorConfig(radius=True, icon="mdi:road-variant")),
                vol.Required(CONF_FORECAST): SelectSelector(
                    SelectSelectorConfig(
                        options=list(FORECAST_TIMES), translation_key=CONF_FORECAST, mode=SelectSelectorMode.DROPDOWN
                    )
                ),
                vol.Required(CONF_ONLY_POOR): BooleanSelector(),
                vol.Required(CONF_REFRESH_SECONDS): REFRESH_SELECTOR,
            }
        )

    def defaults(self) -> dict[str, Any]:
        return {
            CONF_AREA: self.home_area(DEFAULT_ROAD_CONDITION_RADIUS_M),
            CONF_FORECAST: FORECAST_TIMES[0],
            CONF_ONLY_POOR: False,
            CONF_REFRESH_SECONDS: DEFAULT_ROAD_CONDITION_REFRESH_SECONDS,
        }


class WeatherStationFeedFlow(AreaFeedFlow):
    async def async_schema(self) -> vol.Schema:
        return vol.Schema(
            {
                vol.Required(CONF_NAME): TextSelector(),
                vol.Required(CONF_AREA): LocationSelector(LocationSelectorConfig(radius=True, icon="mdi:thermometer")),
                vol.Required(CONF_MARKER_VALUE): SelectSelector(
                    SelectSelectorConfig(
                        options=list(MARKER_VALUES), translation_key=CONF_MARKER_VALUE, mode=SelectSelectorMode.DROPDOWN
                    )
                ),
                vol.Required(CONF_REFRESH_SECONDS): REFRESH_SELECTOR,
            }
        )

    def defaults(self) -> dict[str, Any]:
        return {
            CONF_AREA: self.home_area(DEFAULT_ROAD_RADIUS_M),
            CONF_MARKER_VALUE: DEFAULT_MARKER_VALUE,
            CONF_REFRESH_SECONDS: DEFAULT_WEATHER_STATION_REFRESH_SECONDS,
        }


class WeatherCameraFeedFlow(AreaFeedFlow):
    async def async_schema(self) -> vol.Schema:
        return vol.Schema(
            {
                vol.Required(CONF_NAME): TextSelector(),
                vol.Required(CONF_AREA): LocationSelector(LocationSelectorConfig(radius=True, icon="mdi:cctv")),
                vol.Required(CONF_REFRESH_SECONDS): REFRESH_SELECTOR,
            }
        )

    def defaults(self) -> dict[str, Any]:
        return {
            CONF_AREA: self.home_area(DEFAULT_ROAD_RADIUS_M),
            CONF_REFRESH_SECONDS: DEFAULT_WEATHER_CAMERA_REFRESH_SECONDS,
        }


async def choice_options(
    flow: ConfigSubentryFlow, list_name: str, to_options: Callable[[Any], list[tuple[str, str]]]
) -> list[SelectOptionDict] | SubentryFlowResult:
    """Options for choosing a station or camera from a list the integration keeps; an abort when unavailable."""
    entry = flow._get_entry()
    if entry.state is not ConfigEntryState.LOADED:
        return flow.async_abort(reason="entry_not_loaded")
    shared = getattr(entry.runtime_data, list_name)
    data = await shared.get()
    if not shared.loaded:
        return flow.async_abort(reason="cannot_connect")
    return [SelectOptionDict(value=value, label=label) for value, label in to_options(data)]


class RoadDeviceFlow(ConfigSubentryFlow):
    """Adding one road weather station or camera, which becomes a device. Changing it only changes the update interval.

    The subentry's unique id is the station or camera id, so the same one can't be added twice.
    """

    choice_key: str
    list_name: str
    details_cache: str
    default_refresh_seconds: int
    to_options: Callable[[Any], list[tuple[str, str]]]
    _options: list[SelectOptionDict] | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        if self._options is None:
            options = await choice_options(self, self.list_name, type(self).to_options)
            if isinstance(options, dict):  # an abort result
                return options
            self._options = options

        if user_input is not None:
            chosen = str(user_input[self.choice_key])
            subentry_type = self.handler[1]
            if any(
                subentry.subentry_type == subentry_type and subentry.unique_id == chosen
                for subentry in self._get_entry().subentries.values()
            ):
                return self.async_abort(reason="already_configured")
            return self.async_create_entry(
                title=await self._async_title(chosen),
                data={self.choice_key: chosen, CONF_REFRESH_SECONDS: int(user_input[CONF_REFRESH_SECONDS])},
                unique_id=chosen,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(self.choice_key): SelectSelector(
                        SelectSelectorConfig(options=self._options, mode=SelectSelectorMode.DROPDOWN, sort=False)
                    ),
                    vol.Required(CONF_REFRESH_SECONDS, default=self.default_refresh_seconds): REFRESH_SELECTOR,
                }
            ),
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        subentry = self._get_reconfigure_subentry()
        if user_input is not None:
            return self.async_update_and_abort(
                self._get_entry(),
                subentry,
                data={**subentry.data, CONF_REFRESH_SECONDS: int(user_input[CONF_REFRESH_SECONDS])},
            )
        refresh_seconds = subentry.data.get(CONF_REFRESH_SECONDS, self.default_refresh_seconds)
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema({vol.Required(CONF_REFRESH_SECONDS, default=refresh_seconds): REFRESH_SELECTOR}),
            description_placeholders={"name": subentry.title},
        )

    async def _async_title(self, chosen: str) -> str:
        """The station's or camera's name in the integration's language, or its name in the list."""
        runtime = self._get_entry().runtime_data
        details = getattr(runtime, self.details_cache)
        await details.ensure([chosen])
        if name := details_name(details.get(chosen), runtime.texts.language):
            return name
        label = next((option["label"] for option in self._options or [] if option["value"] == chosen), chosen)
        return label.removesuffix(f" ({chosen})")


class RoadWeatherStationFlow(RoadDeviceFlow):
    choice_key = CONF_STATION
    list_name = "weather_station_list"
    details_cache = "weather_station_details"
    default_refresh_seconds = DEFAULT_WEATHER_STATION_REFRESH_SECONDS
    to_options = staticmethod(station_options)


class WeatherCameraFlow(RoadDeviceFlow):
    choice_key = CONF_CAMERA
    list_name = "camera_list"
    details_cache = "camera_details"
    default_refresh_seconds = DEFAULT_WEATHER_CAMERA_REFRESH_SECONDS
    to_options = staticmethod(camera_options)
