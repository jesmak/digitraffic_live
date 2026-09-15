"""Road weather stations: road and air temperature, road surface, grip, wind and precipitation.

Data: https://tie.digitraffic.fi/swagger/ (weather/v1). Station names come from
each station's details, which are cached; sensor values are fetched every update.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .api import DigitrafficClient
from .cache import DetailCache, fetch_each
from .const import CONF_AREA, CONF_MARKER_VALUE
from .feed import number_text, point_feature, row
from .geo import Area
from .texts import Texts

# The value shown on a station's marker, and the sensor it comes from. Both are in the popup.
MARKER_VALUES = {"air_temperature": "ILMA", "road_temperature": "TIE_1"}
DEFAULT_MARKER_VALUE = "air_temperature"

# Above this many stations in an area, one request for all of Finland is cheaper than one per station.
BULK_THRESHOLD = 25

# Colours for stations that warn about the road: amber for caution, red for ice or an alarm.
CAUTION_COLOR = "#f9a825"
ALARM_COLOR = "#c62828"

# Road surface codes (KELI_1, KELI_2): 0 fault, 1 dry, 2 moist, 3 wet, 4 wet and salty, 5 frost, 6 snow,
# 7 ice, 8 probably moist and salty, 9 slushy.
SURFACE_FAULT = 0
SURFACE_CAUTION = frozenset({5, 6, 9})
SURFACE_ICE = 7
# Warning codes (VAROITUS_1): 0 OK, 1 beware, 2 alarm, 3 frost, 4 rain.
WARNING_ALARM = 2


@dataclass(frozen=True)
class WeatherStationFeedConfig:
    area: Area
    marker_value: str

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> WeatherStationFeedConfig:
        marker_value = data.get(CONF_MARKER_VALUE)
        return cls(
            area=Area.from_selector(data[CONF_AREA]),
            marker_value=marker_value if marker_value in MARKER_VALUES else DEFAULT_MARKER_VALUE,
        )


@dataclass(frozen=True)
class Station:
    id: str
    latitude: float
    longitude: float
    name: str


def stations_in_area(stations: Any, area: Area) -> list[Station]:
    """Stations inside the area that are collecting data, from the station list."""
    result = []
    for feature in (stations or {}).get("features") or []:
        props = feature.get("properties") or {}
        coordinates = (feature.get("geometry") or {}).get("coordinates") or []
        if len(coordinates) < 2 or props.get("collectionStatus") not in (None, "GATHERING"):
            continue
        if area.contains(coordinates[1], coordinates[0]):
            result.append(Station(str(feature.get("id")), coordinates[1], coordinates[0], str(props.get("name") or "")))
    return result


async def fetch_sensor_values(
    client: DigitrafficClient, station_ids: Sequence[str]
) -> dict[str, list[Mapping[str, Any]]]:
    """The latest sensor values of each station, by station id."""
    if len(station_ids) > BULK_THRESHOLD:
        wanted = set(station_ids)
        data = await client.weather_stations_data()
        return {
            str(station.get("id")): station.get("sensorValues") or []
            for station in data.get("stations") or []
            if str(station.get("id")) in wanted
        }
    responses = await fetch_each(station_ids, client.weather_station_data, name="weather station")
    return {station_id: response.get("sensorValues") or [] for station_id, response in responses.items()}


def station_name(station: Station, details: Mapping[str, Any] | None, language: str) -> str:
    """The station's name in the chosen language: "Road 6 Lappeenranta, Kärki"."""
    names = ((details or {}).get("properties") or {}).get("names") or {}
    return names.get(language) or names.get("fi") or station.name.replace("_", " ")


def build_weather_station_features(
    stations: Sequence[Station],
    details: DetailCache[str],
    sensor_values: Mapping[str, Sequence[Mapping[str, Any]]],
    texts: Texts,
    marker_value: str = DEFAULT_MARKER_VALUE,
) -> list[dict[str, Any]]:
    features = []
    for station in stations:
        values = {str(value.get("name")): value for value in sensor_values.get(station.id) or []}
        if not values:
            continue
        marker = numeric(values, MARKER_VALUES.get(marker_value, MARKER_VALUES[DEFAULT_MARKER_VALUE]))
        features.append(
            point_feature(
                f"weather_station:{station.id}",
                station.latitude,
                station.longitude,
                {
                    "name": station_name(station, details.get(station.id), texts.language),
                    "kind": "road.weather_station",
                    "updated": max((str(value.get("measuredTime") or "") for value in values.values()), default=None),
                    "badge": f"{round(marker)}°" if marker is not None else None,
                    "color": station_color(values),
                    "details": station_details(values, texts),
                },
            )
        )
    return features


def numeric(values: Mapping[str, Mapping[str, Any]], name: str) -> float | None:
    value = (values.get(name) or {}).get("value")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


def surface_code(values: Mapping[str, Mapping[str, Any]]) -> int | None:
    """The road surface from the first surface sensor, or the second when the first reports a fault."""
    for name in ("KELI_1", "KELI_2"):
        code = numeric(values, name)
        if code is not None and int(code) != SURFACE_FAULT:
            return int(code)
    return None


def station_color(values: Mapping[str, Mapping[str, Any]]) -> str | None:
    surface = surface_code(values)
    warning = numeric(values, "VAROITUS_1")
    if surface == SURFACE_ICE or (warning is not None and int(warning) == WARNING_ALARM):
        return ALARM_COLOR
    if surface in SURFACE_CAUTION or (warning is not None and int(warning) > 0):
        return CAUTION_COLOR
    return None


def station_details(values: Mapping[str, Mapping[str, Any]], texts: Texts) -> list[dict[str, Any]]:
    rows = []

    def measurement(name: str, label: str, unit: str, decimals: int = 1, skip_zero: bool = False) -> None:
        value = numeric(values, name)
        if value is not None and not (skip_zero and value == 0):
            rows.append(row(texts(label), number_text(value, decimals), unit))

    def coded(name: str, label: str, prefix: str, code: int | None = None, skip: int | None = None) -> None:
        if code is None:
            value = numeric(values, name)
            code = int(value) if value is not None else None
        if code is not None and code != skip and texts.has(f"{prefix}_{code}"):
            rows.append(row(texts(label), texts(f"{prefix}_{code}")))

    measurement("TIE_1", "road_temperature", "°C")
    measurement("ILMA", "air_temperature", "°C")
    coded("KELI_1", "road_surface", "surface_code", code=surface_code(values))
    coded("VAROITUS_1", "warning", "warning_code", skip=0)
    measurement("KITKA1", "friction", "µ", decimals=2)
    measurement("LUMEN_MÄÄRÄ1", "snow_on_road", "mm", skip_zero=True)
    measurement("JÄÄN_MÄÄRÄ1", "ice_on_road", "mm", skip_zero=True)
    measurement("KESKITUULI", "wind_speed", "m/s")
    measurement("MAKSIMITUULI", "gusts", "m/s")
    coded("SADE", "precipitation", "rain_code")
    measurement("SADE_INTENSITEETTI", "rain_intensity", "mm/h", skip_zero=True)
    measurement("NÄKYVYYS_KM", "visibility", "km")
    measurement("ILMAN_KOSTEUS", "humidity", "%", decimals=0)
    return rows
