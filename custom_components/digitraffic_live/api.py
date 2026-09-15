"""HTTP client for the Digitraffic marine, railway and road APIs.

API documentation:
  marine:  https://meri.digitraffic.fi/swagger/
  railway: https://rata.digitraffic.fi/swagger/ and https://rata.digitraffic.fi/api/v2/graphql/graphiql
  road:    https://tie.digitraffic.fi/swagger/
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import aiohttp

MARINE_API = "https://meri.digitraffic.fi/api"
RAILWAY_API = "https://rata.digitraffic.fi/api"
ROAD_API = "https://tie.digitraffic.fi/api"

# Traffic message types and their paths in the road API.
TRAFFIC_MESSAGE_PATHS = {
    "road_works": "roadworks",
    "traffic_announcements": "traffic-announcements",
    "weight_restrictions": "weight-restrictions",
    "exempted_transports": "exempted-transports",
}

type BoundingBox = tuple[float, float, float, float]  # west, south, east, north

REQUEST_TIMEOUT_SECONDS = 30


class DigitrafficError(Exception):
    """A request to Digitraffic failed."""


class DigitrafficNotFound(DigitrafficError):
    """Digitraffic has no data for the request (HTTP 404)."""


class DigitrafficClient:
    """Async JSON client for Digitraffic.

    Every request carries a Digitraffic-User header, as Digitraffic's terms ask.
    aiohttp negotiates the gzip compression Digitraffic requires.
    """

    def __init__(self, session: aiohttp.ClientSession, user: str) -> None:
        self._session = session
        self._user = user

    # ---------------- marine ----------------

    async def ais_locations(
        self,
        since_ms: int,
        latitude: float | None = None,
        longitude: float | None = None,
        radius_km: int | None = None,
    ) -> dict[str, Any]:
        """Latest AIS positions received after `since_ms`, optionally within a circle."""
        params = {"from": str(since_ms)}
        if latitude is not None and longitude is not None and radius_km is not None:
            params |= {
                "latitude": f"{latitude:.5f}",
                "longitude": f"{longitude:.5f}",
                "radius": str(radius_km),
            }
        return await self._request("GET", f"{MARINE_API}/ais/v1/locations", params=params)

    async def vessel(self, mmsi: int) -> dict[str, Any]:
        """Register data (name, type, destination…) for one vessel."""
        return await self._request("GET", f"{MARINE_API}/ais/v1/vessels/{mmsi}")

    async def vessels(self) -> list[dict[str, Any]]:
        """Register data for every vessel."""
        return await self._request("GET", f"{MARINE_API}/ais/v1/vessels")

    async def winter_navigation_vessels(self) -> dict[str, Any]:
        """Icebreakers and the vessels they assist."""
        return await self._request("GET", f"{MARINE_API}/winter-navigation/v2/vessels")

    # ---------------- railway ----------------

    async def running_trains(self, query: str) -> list[dict[str, Any]]:
        """Runs a `currentlyRunningTrains` GraphQL query and returns the trains."""
        response = await self._request("POST", f"{RAILWAY_API}/v2/graphql/graphql", body={"query": query})
        if errors := response.get("errors"):
            raise DigitrafficError("; ".join(str(error.get("message")) for error in errors))
        return (response.get("data") or {}).get("currentlyRunningTrains") or []

    async def passenger_information(self) -> list[dict[str, Any]]:
        """Active passenger information messages."""
        return await self._request("GET", f"{RAILWAY_API}/v1/passenger-information/active")

    async def composition(self, departure_date: str, train_number: int) -> dict[str, Any]:
        """Cars and services of one train run. Raises DigitrafficNotFound for trains without one."""
        return await self._request("GET", f"{RAILWAY_API}/v1/compositions/{departure_date}/{train_number}")

    async def stations(self) -> list[dict[str, Any]]:
        """Every station and stop, with names and short codes."""
        return await self._request("GET", f"{RAILWAY_API}/v1/metadata/stations")

    # ---------------- road ----------------

    async def traffic_messages(self, message_type: str, bbox: BoundingBox, until: str | None) -> dict[str, Any]:
        """Active traffic messages of one type (see TRAFFIC_MESSAGE_PATHS) inside a bounding box.

        Road works starting before `until` (ISO 8601) are included; without it, all known ones are.
        """
        params = bbox_params(bbox)
        if until:
            params.append(("to", until))
        return await self._request(
            "GET", f"{ROAD_API}/traffic-message/v2/{TRAFFIC_MESSAGE_PATHS[message_type]}", params=params
        )

    async def maintenance_latest(self, bbox: BoundingBox, end_from: str, tasks: Iterable[str]) -> dict[str, Any]:
        """The latest position of each maintenance vehicle that has worked since `end_from`."""
        params = [*bbox_params(bbox), ("endFrom", end_from), *(("taskId", task) for task in tasks)]
        return await self._request("GET", f"{ROAD_API}/maintenance/v1/tracking/routes/latest", params=params)

    async def maintenance_routes(self, bbox: BoundingBox, end_from: str, tasks: Iterable[str]) -> dict[str, Any]:
        """Where maintenance vehicles have worked since `end_from` (at most 24 hours ago)."""
        params = [*bbox_params(bbox), ("endFrom", end_from), *(("taskId", task) for task in tasks)]
        return await self._request("GET", f"{ROAD_API}/maintenance/v1/tracking/routes", params=params)

    async def maintenance_tasks(self) -> list[dict[str, Any]]:
        """Maintenance task ids with their names in Finnish, Swedish and English."""
        return await self._request("GET", f"{ROAD_API}/maintenance/v1/tracking/tasks")

    async def forecast_sections(self) -> dict[str, Any]:
        """Road sections that have a road weather forecast, with their geometry."""
        return await self._request("GET", f"{ROAD_API}/weather/v1/forecast-sections-simple")

    async def forecasts(self, bbox: BoundingBox) -> dict[str, Any]:
        """Current observation and forecasts for the road sections inside a bounding box."""
        return await self._request(
            "GET", f"{ROAD_API}/weather/v1/forecast-sections-simple/forecasts", params=bbox_params(bbox)
        )

    async def weather_stations(self) -> dict[str, Any]:
        """Every road weather station, with its position."""
        return await self._request("GET", f"{ROAD_API}/weather/v1/stations")

    async def weather_station(self, station_id: str) -> dict[str, Any]:
        """One road weather station, with its names in Finnish, Swedish and English."""
        return await self._request("GET", f"{ROAD_API}/weather/v1/stations/{station_id}")

    async def weather_station_data(self, station_id: str) -> dict[str, Any]:
        """The latest sensor values of one road weather station."""
        return await self._request("GET", f"{ROAD_API}/weather/v1/stations/{station_id}/data")

    async def weather_stations_data(self) -> dict[str, Any]:
        """The latest sensor values of every road weather station (several megabytes)."""
        return await self._request("GET", f"{ROAD_API}/weather/v1/stations/data")

    async def weathercam_stations(self) -> dict[str, Any]:
        """Every road weather camera, with its position."""
        return await self._request("GET", f"{ROAD_API}/weathercam/v1/stations")

    async def weathercam_station(self, station_id: str) -> dict[str, Any]:
        """One road weather camera, with its names and the names of its views."""
        return await self._request("GET", f"{ROAD_API}/weathercam/v1/stations/{station_id}")

    async def weathercam_station_data(self, station_id: str) -> dict[str, Any]:
        """When each view of one camera was last photographed."""
        return await self._request("GET", f"{ROAD_API}/weathercam/v1/stations/{station_id}/data")

    async def weathercam_stations_data(self) -> dict[str, Any]:
        """When each view of every camera was last photographed."""
        return await self._request("GET", f"{ROAD_API}/weathercam/v1/stations/data")

    # ---------------- plumbing ----------------

    async def _request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, str] | Sequence[tuple[str, str]] | None = None,
        body: dict[str, Any] | None = None,
    ) -> Any:
        headers = {"Digitraffic-User": self._user, "Accept-Encoding": "gzip"}
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT_SECONDS):
                async with self._session.request(method, url, params=params, json=body, headers=headers) as response:
                    if response.status == 404:
                        raise DigitrafficNotFound(f"No data at {url}")
                    if response.status != 200:
                        raise DigitrafficError(f"HTTP {response.status} from {url}")
                    return await response.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise DigitrafficError(f"Request to {url} failed: {err!r}") from err


def bbox_params(bbox: BoundingBox) -> list[tuple[str, str]]:
    west, south, east, north = bbox
    return [("xMin", str(west)), ("yMin", str(south)), ("xMax", str(east)), ("yMax", str(north))]
