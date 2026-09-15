"""Road data: geometry helpers, and building traffic message, maintenance, road condition,
weather station and weather camera feeds from sample Digitraffic responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.util import dt as dt_util

from custom_components.digitraffic_live.api import DigitrafficError
from custom_components.digitraffic_live.cache import DetailCache
from custom_components.digitraffic_live.geo import Area, representative_position, simplify_path
from custom_components.digitraffic_live.maintenance import (
    MaintenanceFeedConfig,
    build_maintenance_features,
    fetch_maintenance,
    merge_routes,
    task_names,
)
from custom_components.digitraffic_live.road_conditions import (
    RoadConditionFeedConfig,
    build_road_condition_features,
    count_poor,
    section_index,
)
from custom_components.digitraffic_live.texts import load_texts
from custom_components.digitraffic_live.traffic_messages import (
    TrafficMessageFeedConfig,
    build_traffic_message_features,
    fetch_traffic_messages,
    working_hours,
)
from custom_components.digitraffic_live.weather_cameras import (
    build_weather_camera_features,
    camera_options,
    cameras_in_area,
    fetch_picture_times,
    picture_times,
    views_in_collection,
)
from custom_components.digitraffic_live.weather_stations import (
    build_weather_station_features,
    fetch_sensor_values,
    station_color,
    station_options,
    station_readings,
    stations_in_area,
)

from .conftest import ROAD_AREA, road_fixture

NOW = datetime(2026, 9, 15, 12, 0, tzinfo=dt_util.UTC)
TEXTS = load_texts("en")


def fixture(name: str) -> Any:
    return road_fixture(name)


def area() -> Area:
    return Area.from_selector(ROAD_AREA)


class FakeRoadClient:
    """Answers road API calls from the fixtures and records them."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple]] = []

    async def traffic_messages(self, message_type: str, bbox: Any, until: str | None) -> Any:
        self.calls.append(("traffic_messages", (message_type, bbox, until)))
        return fixture(message_type)

    async def maintenance_latest(self, bbox: Any, end_from: str, tasks: Any) -> Any:
        self.calls.append(("maintenance_latest", (end_from, tuple(tasks))))
        return fixture("maintenance_latest")

    async def maintenance_routes(self, bbox: Any, end_from: str, tasks: Any) -> Any:
        self.calls.append(("maintenance_routes", (end_from, tuple(tasks))))
        return fixture("maintenance_routes")

    async def weather_station(self, station_id: str) -> Any:
        if station_id != "3036":
            raise DigitrafficError("no details")
        return fixture("weather_station_3036")

    async def weather_station_data(self, station_id: str) -> Any:
        if station_id != "3036":
            raise DigitrafficError("no data")
        return fixture("weather_station_3036_data")

    async def weathercam_station(self, station_id: str) -> Any:
        return fixture(f"weathercam_{station_id}")

    async def weathercam_station_data(self, station_id: str) -> Any:
        return fixture(f"weathercam_{station_id}_data")


# ---------------- geometry ----------------


def test_an_area_touches_lines_that_cross_it_without_a_point_inside() -> None:
    circle = Area(60.9, 27.6, 5)
    crossing = {"type": "LineString", "coordinates": [[27.4, 60.9], [27.8, 60.9]]}
    beside = {"type": "LineString", "coordinates": [[27.4, 61.2], [27.8, 61.2]]}
    around = {"type": "Polygon", "coordinates": [[[27, 60.5], [28.2, 60.5], [28.2, 61.3], [27, 61.3], [27, 60.5]]]}
    assert circle.touches(crossing)
    assert not circle.touches(beside)
    assert circle.touches(around), "a circle inside a large polygon touches it"
    assert circle.touches({"type": "Point", "coordinates": [27.6, 60.92]})
    assert not circle.touches(None)


def test_bounding_box_stays_within_what_digitraffic_accepts() -> None:
    west, south, east, north = Area(60.9, 27.6, 60).bbox()
    assert west < 27.6 < east and south < 60.9 < north
    assert Area(59.1, 19.1, 500).bbox()[:2] == (19.0, 59.0)


def test_simplifying_keeps_the_shape_and_drops_points_on_a_straight_line() -> None:
    straight = [[27.0 + i / 100, 60.0] for i in range(101)]
    assert simplify_path(straight, 0.01) == [[27.0, 60.0], [28.0, 60.0]]
    corner = [[27.0, 60.0], [27.5, 60.0], [27.5, 60.5]]
    assert simplify_path(corner, 0.01) == corner


def test_representative_position_is_the_middle_of_the_longest_line() -> None:
    lines = {"type": "MultiLineString", "coordinates": [[[27, 60], [27.01, 60]], [[27, 61], [27.5, 61], [28, 61]]]}
    assert representative_position(lines) == (61, 27.5)


# ---------------- traffic messages ----------------


async def test_traffic_messages_are_fetched_per_type_and_limited_to_the_area() -> None:
    client = FakeRoadClient()
    config = TrafficMessageFeedConfig.from_data({"area": ROAD_AREA, "message_types": [], "upcoming_days": 7})
    situations = await fetch_traffic_messages(client, config, NOW)

    assert [call[1][0] for call in client.calls] == [
        "road_works",
        "traffic_announcements",
        "weight_restrictions",
        "exempted_transports",
    ]
    assert client.calls[0][1][2] == "2026-09-22T12:00:00Z"
    # Two road works nearby (a third is far away), the accident and the exempted transport's area.
    assert len(situations) == 4


async def test_traffic_message_features() -> None:
    config = TrafficMessageFeedConfig.from_data(
        {"area": ROAD_AREA, "message_types": ["road_works", "traffic_announcements"]}
    )
    situations = await fetch_traffic_messages(FakeRoadClient(), config, NOW)
    features = build_traffic_message_features(situations, TEXTS, NOW)
    by_id = {feature["id"]: feature for feature in features}

    road_work = next(feature for feature in features if feature["properties"].get("name", "").startswith("Tie 26"))
    props = road_work["properties"]
    assert props["kind"] == "road.roadwork"
    assert props["name"] == "Tie 26, Hamina, Luumäki. Tietyö"
    assert props["subtitle"] == "Tie 26 välillä Hamina - Lappeenranta."
    details = {item["label"]: item["value"] for item in props["details"]}
    assert details["Status"].startswith("starts ")
    assert details["Working hours"] == "Mon–Fri 18:00–06:00"
    assert details["Restrictions"] == "One lane closed, Slow-moving works vehicle"
    assert "Roadside equipment" in details["Work"]

    area_feature = by_id[f"{road_work['id']}/area"]
    assert area_feature["geometry"]["type"] == "MultiLineString"
    assert area_feature["properties"] == {"kind": "road.roadwork", "point": road_work["id"]}

    accident = [feature for feature in features if feature["properties"].get("kind") == "road.accident"]
    assert len(accident) == 1
    assert accident[0]["geometry"]["type"] == "Point"


def test_working_hours_group_days_with_the_same_hours() -> None:
    hours = [
        {"weekday": "Friday", "startTime": "07:00", "endTime": "15:00"},
        {"weekday": "Monday", "startTime": "07:00", "endTime": "15:00"},
        {"weekday": "Saturday", "startTime": "09:00", "endTime": "13:00"},
    ]
    assert working_hours(hours, load_texts("fi")) == "ma, pe 07.00–15.00; la 09.00–13.00"
    weekdays = [
        {"weekday": day, "startTime": "18:00", "endTime": "06:00"} for day in ("Wednesday", "Monday", "Tuesday")
    ]
    assert working_hours(weekdays, load_texts("en")) == "Mon–Wed 18:00–06:00"


# ---------------- maintenance ----------------


async def test_maintenance_routes_are_requested_only_when_shown() -> None:
    client = FakeRoadClient()
    hidden = MaintenanceFeedConfig.from_data({"area": ROAD_AREA, "show_routes": False, "max_age_minutes": 30})
    vehicles, routes = await fetch_maintenance(client, hidden, NOW)
    assert [call[0] for call in client.calls] == ["maintenance_latest"]
    assert client.calls[0][1] == ("2026-09-15T11:30:00Z", ())
    assert len(vehicles) == 2 and routes == []

    client.calls.clear()
    shown = MaintenanceFeedConfig.from_data({"area": ROAD_AREA, "tasks": ["salting"], "route_hours": 99})
    assert shown.route_hours == 24
    await fetch_maintenance(client, shown, NOW)
    assert client.calls[1] == ("maintenance_routes", ("2026-09-14T12:00:00Z", ("SALTING",)))


def test_route_pieces_of_the_same_work_are_joined() -> None:
    chains = merge_routes(fixture("maintenance_routes")["features"])
    assert [chain.tasks for chain in chains] == [("LEVELLING_GRAVEL_ROAD_SURFACE",), ("SPREADING_OF_CRUSH",)] or [
        chain.tasks for chain in chains
    ] == [("SPREADING_OF_CRUSH",), ("LEVELLING_GRAVEL_ROAD_SURFACE",)]
    crush = next(chain for chain in chains if chain.tasks == ("SPREADING_OF_CRUSH",))
    assert crush.first_id == 200125740
    assert crush.end == fixture("maintenance_routes")["features"][2]["properties"]["endTime"]


def test_maintenance_features() -> None:
    names = task_names(fixture("maintenance_tasks"), "en")
    latest = fixture("maintenance_latest")["features"]
    features = build_maintenance_features(latest, fixture("maintenance_routes")["features"], names, TEXTS)
    vehicles = [feature for feature in features if feature["geometry"]["type"] == "Point"]
    routes = [feature for feature in features if feature["geometry"]["type"] != "Point"]

    assert len(vehicles) == 2
    first = vehicles[0]["properties"]
    assert first["kind"] == "road.maintenance"
    assert first["name"] == names[latest[0]["properties"]["tasks"][0]]
    assert first["details"][-1] == {"label": "Source", "value": "Harja/Väylävirasto"}
    assert len(routes) == 2
    assert {route["properties"]["kind"] for route in routes} == {"road.maintenance_track"}


# ---------------- road conditions ----------------


def test_road_condition_features() -> None:
    sections = section_index(fixture("forecast_sections"))
    now = RoadConditionFeedConfig.from_data({"area": ROAD_AREA})
    features = build_road_condition_features(fixture("forecasts"), sections, now, TEXTS)
    assert len(features) == 2
    assert count_poor(features) == 0

    later = RoadConditionFeedConfig.from_data({"area": ROAD_AREA, "forecast": "2h", "only_poor": True})
    [poor] = build_road_condition_features(fixture("forecasts"), sections, later, TEXTS)
    props = poor["properties"]
    assert props["kind"] == "road.condition.poor"
    assert props["subtitle"].startswith("Forecast for ")
    details = {item["label"]: item["value"] for item in props["details"]}
    assert details["Driving conditions"] == "Poor"
    assert details["Road surface"] == "Ice"
    assert details["Grip"] == "Slippery"
    assert count_poor([poor]) == 1


# ---------------- weather stations and cameras ----------------


async def test_weather_station_features() -> None:
    client = FakeRoadClient()
    stations = stations_in_area(fixture("weather_stations"), area())
    assert [station.id for station in stations] == ["3036", "5007"]

    details = DetailCache("weather station", client.weather_station)
    await details.ensure([station.id for station in stations])
    values = await fetch_sensor_values(client, [station.id for station in stations])
    [feature] = build_weather_station_features(stations, details, values, TEXTS)
    [road] = build_weather_station_features(stations, details, values, TEXTS, "road_temperature")
    assert road["properties"]["badge"] == "23°"

    props = feature["properties"]
    assert feature["id"] == "weather_station:3036"
    assert props["name"] == "Road 6 Lappeenranta, Kärki"
    assert props["kind"] == "road.weather_station"
    assert props["badge"] == "15°", "air temperature by default"
    assert "color" not in props
    details_by_label = {item["label"]: item for item in props["details"]}
    assert details_by_label["Road temperature"] == {"label": "Road temperature", "value": "22.9", "unit": "°C"}
    assert details_by_label["Road surface"]["value"] == "Dry"


def test_station_colour_warns_about_ice_and_uses_the_second_sensor_on_a_fault() -> None:
    def values(**sensors: float) -> dict[str, dict[str, float]]:
        return {name: {"value": value} for name, value in sensors.items()}

    assert station_color(values(KELI_1=1, VAROITUS_1=0)) is None
    assert station_color(values(KELI_1=7)) == "#c62828"
    assert station_color(values(KELI_1=0, KELI_2=6)) == "#f9a825"
    assert station_color(values(KELI_1=1, VAROITUS_1=2)) == "#c62828"


async def test_weather_camera_features() -> None:
    client = FakeRoadClient()
    cameras = cameras_in_area(fixture("weathercam_stations"), area())
    assert [camera.id for camera in cameras] == ["C03558"]

    details = DetailCache("weather camera", client.weathercam_station)
    await details.ensure(["C03558"])
    times = await fetch_picture_times(client, ["C03558"])
    [feature] = build_weather_camera_features(cameras, details, times, "en")

    props = feature["properties"]
    assert props["name"] == "Road 6 Lappeenranta, Saimaa channel"
    assert props["kind"] == "road.camera"
    first = props["images"][0]
    assert first["url"].startswith("https://weathercam.digitraffic.fi/C0355801.jpg?t=")
    assert first["caption"] == "Imatralle"
    assert len(props["images"]) == 3


def test_station_readings() -> None:
    values = {value["name"]: value for value in fixture("weather_station_3036_data")["sensorValues"]}
    assert station_readings(values) == {
        "road_temperature": 22.9,
        "air_temperature": 14.6,
        "road_surface": "dry",
        "grip": 0.82,
        "road_warning": "ok",
    }


def test_each_value_comes_from_the_first_sensor_that_has_one() -> None:
    def values(**sensors: float) -> dict[str, dict[str, float]]:
        return {name.replace("DST_ANT", "DST-ANT"): {"value": value} for name, value in sensors.items()}

    # Many stations lack sensor 1 and have only sensor 2, or only optical sensors.
    lane_two = station_readings(values(TIE_2=-0.6, KELI_1=0, KELI_2=7, VAROITUS_2=2, KITKA2=0.31))
    assert lane_two == {
        "road_temperature": -0.6,
        "air_temperature": None,
        "road_surface": "ice",
        "grip": 0.31,
        "road_warning": "alarm",
    }
    optical = station_readings(
        values(TIEN_LÄMPÖTILA_DST_ANT=-1.4, ILMA=2.0, OPTISEN_ANTURIN_KELI1=5, OPTISEN_ANTURIN_VAROITUS1=3)
    )
    assert optical["road_temperature"] == -1.4
    assert optical["road_surface"] == "frost"
    assert optical["road_warning"] == "frost"
    assert optical["grip"] is None
    assert station_color(values(TIE_2=-0.6, KELI_2=7)) == "#c62828"

    [feature] = build_weather_station_features(
        stations_in_area(fixture("weather_stations"), area())[:1],
        DetailCache("weather station", FakeRoadClient().weather_station),
        {"3036": [{"name": "TIEN_LÄMPÖTILA_DST-ANT", "value": -1.4}]},
        TEXTS,
        "road_temperature",
    )
    assert feature["properties"]["badge"] == "-1°"
    assert feature["properties"]["details"][0]["value"] == "-1.4"


def test_station_and_camera_choices() -> None:
    assert station_options(fixture("weather_stations")) == [
        ("3036", "vt6 Lappeenranta Kärki (3036)"),
        ("5007", "vt6 Luumäki kko (5007)"),
        ("2002", "vt8 Pyhäranta Ihode (2002)"),
    ]
    assert camera_options(fixture("weathercam_stations")) == [("C03558", "vt6 Lappeenranta Saimaan kanava (C03558)")]


def test_camera_views_and_picture_times() -> None:
    assert views_in_collection(fixture("weathercam_C03558")) == ("C0355801", "C0355802", "C0355809")
    times = picture_times(fixture("weathercam_C03558_data"))
    assert times["C0355801"] == "2026-09-15T11:47:33Z"
    assert len(times) == 3
