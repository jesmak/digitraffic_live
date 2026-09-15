"""Shared fixtures: sample Digitraffic responses and a mocked API."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.digitraffic_live.api import MARINE_API, RAILWAY_API, ROAD_API, TRAFFIC_MESSAGE_PATHS

HAMINA_AREA = {"latitude": 60.569, "longitude": 27.198, "radius": 15000}
# Luumäki, between Lappeenranta and Hamina: the road fixtures are around it.
ROAD_AREA = {"latitude": 60.9, "longitude": 27.6, "radius": 60000}
FIXTURES = Path(__file__).parent / "fixtures"


def road_fixture(name: str) -> Any:
    """A trimmed real road API response from tests/fixtures."""
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Lets Home Assistant load integrations from custom_components/."""


def now_ms() -> int:
    return int(dt_util.utcnow().timestamp() * 1000)


def ais_locations() -> dict[str, Any]:
    """A pilot boat under way and a moored cargo ship near the cabin, and a ship far away."""
    received = now_ms()
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "geometry": {"type": "Point", "coordinates": [27.17, 60.53]},
                "properties": {
                    "mmsi": 111,
                    "sog": 11,
                    "cog": 90,
                    "heading": 88,
                    "navStat": 0,
                    "timestampExternal": received,
                },
            },
            {
                "geometry": {"type": "Point", "coordinates": [27.2, 60.52]},
                "properties": {
                    "mmsi": 222,
                    "sog": 0,
                    "cog": 0,
                    "heading": 511,
                    "navStat": 5,
                    "timestampExternal": received,
                },
            },
            {
                "geometry": {"type": "Point", "coordinates": [28.5, 61.5]},
                "properties": {
                    "mmsi": 333,
                    "sog": 5,
                    "cog": 10,
                    "heading": 10,
                    "navStat": 0,
                    "timestampExternal": received,
                },
            },
        ],
    }


VESSELS: dict[int, dict[str, Any]] = {
    111: {
        "mmsi": 111,
        "name": "PILOT L117",
        "shipType": 50,
        "draught": 22,
        "imo": 0,
        "callSign": "OJ1234",
        "referencePointA": 8,
        "referencePointB": 5,
        "referencePointC": 2,
        "referencePointD": 2,
    },
    222: {"mmsi": 222, "name": "KOTKA", "shipType": 70, "destination": "FIHMN"},
}


def running_trains() -> dict[str, Any]:
    now = dt_util.utcnow().isoformat()
    return {
        "data": {
            "currentlyRunningTrains": [
                {
                    "trainNumber": 8,
                    "departureDate": "2026-09-14",
                    "cancelled": False,
                    "trainType": {"name": "IC", "trainCategory": {"name": "Long-distance"}},
                    "trainLocations": [{"speed": 113, "timestamp": now, "location": [27.3, 60.9]}],
                    "last": [{"station": {"name": "Kaitjärvi"}, "differenceInMinutes": 11, "actualTime": now}],
                    "next": [
                        {
                            "station": {"name": "Kouvola asema"},
                            "scheduledTime": now,
                            "differenceInMinutes": 11,
                            "commercialTrack": "6",
                        }
                    ],
                    "first": [{"station": {"name": "Joensuu asema"}}],
                    "destination": [{"station": {"name": "Helsinki asema"}}],
                }
            ]
        }
    }


PASSENGER_INFORMATION = [
    {"trainNumber": 8, "trainDepartureDate": "2026-09-14", "video": {"text": {"en": "Delayed by track works."}}}
]

COMPOSITION = {
    "journeySections": [
        {"maximumSpeed": 200, "wagons": [{"pet": True}, {"catering": True}, {}, {}, {}]},
    ]
}

STATIONS = [
    {"stationName": "Helsinki asema", "stationShortCode": "HKI", "passengerTraffic": True},
    {"stationName": "Lappeenranta", "stationShortCode": "LR", "passengerTraffic": True},
    {"stationName": "Ahonpää", "stationShortCode": "AHO", "passengerTraffic": False},
]


@pytest.fixture
def digitraffic_api(aioclient_mock: AiohttpClientMocker) -> AiohttpClientMocker:
    """Every Digitraffic endpoint the integration uses, answering with the samples above."""
    aioclient_mock.get(f"{MARINE_API}/ais/v1/locations", json=ais_locations())
    for mmsi, vessel in VESSELS.items():
        aioclient_mock.get(f"{MARINE_API}/ais/v1/vessels/{mmsi}", json=vessel)
    aioclient_mock.get(f"{MARINE_API}/ais/v1/vessels/333", status=404)
    aioclient_mock.get(f"{MARINE_API}/winter-navigation/v2/vessels", json={"vessels": []})
    aioclient_mock.post(f"{RAILWAY_API}/v2/graphql/graphql", json=running_trains())
    aioclient_mock.get(f"{RAILWAY_API}/v1/passenger-information/active", json=PASSENGER_INFORMATION)
    aioclient_mock.get(f"{RAILWAY_API}/v1/compositions/2026-09-14/8", json=COMPOSITION)
    aioclient_mock.get(f"{RAILWAY_API}/v1/compositions/2026-09-14/9", status=404)
    aioclient_mock.get(f"{RAILWAY_API}/v1/metadata/stations", json=STATIONS)
    return aioclient_mock


@pytest.fixture
def road_api(aioclient_mock: AiohttpClientMocker) -> AiohttpClientMocker:
    """Every road API endpoint the integration uses, answering with the fixtures."""
    for message_type, path in TRAFFIC_MESSAGE_PATHS.items():
        aioclient_mock.get(f"{ROAD_API}/traffic-message/v2/{path}", json=road_fixture(message_type))
    aioclient_mock.get(f"{ROAD_API}/maintenance/v1/tracking/routes/latest", json=road_fixture("maintenance_latest"))
    aioclient_mock.get(f"{ROAD_API}/maintenance/v1/tracking/routes", json=road_fixture("maintenance_routes"))
    aioclient_mock.get(f"{ROAD_API}/maintenance/v1/tracking/tasks", json=road_fixture("maintenance_tasks"))
    aioclient_mock.get(f"{ROAD_API}/weather/v1/forecast-sections-simple/forecasts", json=road_fixture("forecasts"))
    aioclient_mock.get(f"{ROAD_API}/weather/v1/forecast-sections-simple", json=road_fixture("forecast_sections"))
    aioclient_mock.get(f"{ROAD_API}/weather/v1/stations/3036/data", json=road_fixture("weather_station_3036_data"))
    aioclient_mock.get(f"{ROAD_API}/weather/v1/stations/3036", json=road_fixture("weather_station_3036"))
    aioclient_mock.get(f"{ROAD_API}/weather/v1/stations/5007/data", status=404)
    aioclient_mock.get(f"{ROAD_API}/weather/v1/stations/5007", status=404)
    aioclient_mock.get(f"{ROAD_API}/weather/v1/stations", json=road_fixture("weather_stations"))
    aioclient_mock.get(f"{ROAD_API}/weathercam/v1/stations/C03558/data", json=road_fixture("weathercam_C03558_data"))
    aioclient_mock.get(f"{ROAD_API}/weathercam/v1/stations/C03558", json=road_fixture("weathercam_C03558"))
    aioclient_mock.get(f"{ROAD_API}/weathercam/v1/stations", json=road_fixture("weathercam_stations"))
    return aioclient_mock
