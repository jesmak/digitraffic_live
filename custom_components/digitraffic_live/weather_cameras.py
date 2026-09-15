"""Road weather cameras: the latest picture from each of a camera's views.

Data: https://tie.digitraffic.fi/swagger/ (weathercam/v1). Pictures are taken
about every ten minutes. View names come from each camera's details, which are cached.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from homeassistant.util import dt as dt_util

from .api import DigitrafficClient
from .cache import DetailCache, fetch_each
from .const import CONF_AREA
from .feed import point_feature
from .geo import Area

IMAGE_URL = "https://weathercam.digitraffic.fi/{preset}.jpg"

# Above this many cameras in an area, one request for all of Finland is cheaper than one per camera.
BULK_THRESHOLD = 25


@dataclass(frozen=True)
class WeatherCameraFeedConfig:
    area: Area

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> WeatherCameraFeedConfig:
        return cls(area=Area.from_selector(data[CONF_AREA]))


@dataclass(frozen=True)
class Camera:
    id: str
    latitude: float
    longitude: float
    name: str
    presets: tuple[str, ...]


def cameras_in_area(stations: Any, area: Area) -> list[Camera]:
    """Cameras inside the area that are taking pictures, with the views being photographed."""
    result = []
    for feature in (stations or {}).get("features") or []:
        props = feature.get("properties") or {}
        coordinates = (feature.get("geometry") or {}).get("coordinates") or []
        if len(coordinates) < 2 or props.get("collectionStatus") not in (None, "GATHERING"):
            continue
        presets = tuple(
            str(preset["id"])
            for preset in props.get("presets") or []
            if preset.get("inCollection") and preset.get("id")
        )
        if presets and area.contains(coordinates[1], coordinates[0]):
            result.append(
                Camera(str(feature.get("id")), coordinates[1], coordinates[0], str(props.get("name") or ""), presets)
            )
    return result


async def fetch_picture_times(client: DigitrafficClient, camera_ids: Sequence[str]) -> dict[str, dict[str, str]]:
    """When each view was last photographed: {camera id: {preset id: time}}."""
    if len(camera_ids) > BULK_THRESHOLD:
        wanted = set(camera_ids)
        data = await client.weathercam_stations_data()
        stations = [station for station in data.get("stations") or [] if str(station.get("id")) in wanted]
    else:
        stations = list((await fetch_each(camera_ids, client.weathercam_station_data, name="weather camera")).values())
    return {
        str(station.get("id")): {
            str(preset.get("id")): str(preset.get("measuredTime"))
            for preset in station.get("presets") or []
            if preset.get("measuredTime")
        }
        for station in stations
    }


def build_weather_camera_features(
    cameras: Sequence[Camera],
    details: DetailCache[str],
    picture_times: Mapping[str, Mapping[str, str]],
    language: str,
) -> list[dict[str, Any]]:
    features = []
    for camera in cameras:
        props = (details.get(camera.id) or {}).get("properties") or {}
        names = props.get("names") or {}
        view_names = {str(preset.get("id")): preset.get("presentationName") for preset in props.get("presets") or []}
        times = picture_times.get(camera.id) or {}
        images = [picture(preset, view_names.get(preset), times.get(preset)) for preset in camera.presets]
        features.append(
            point_feature(
                f"camera:{camera.id}",
                camera.latitude,
                camera.longitude,
                {
                    "name": names.get(language) or names.get("fi") or camera.name.replace("_", " "),
                    "kind": "road.camera",
                    "updated": max(times.values(), default=None),
                    "images": images,
                },
            )
        )
    return features


def picture(preset: str, view_name: Any, taken: str | None) -> dict[str, Any]:
    """A picture for the popup. The time in the URL makes the browser load a new picture when there is one."""
    url = IMAGE_URL.format(preset=preset)
    moment = dt_util.parse_datetime(taken) if taken else None
    if moment is not None:
        url += f"?t={int(moment.timestamp())}"
    result: dict[str, Any] = {"url": url}
    if view_name:
        result["caption"] = str(view_name)
    if taken:
        result["time"] = taken
    return result
