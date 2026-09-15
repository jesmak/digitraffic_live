"""Ship data interpretation and feed building."""

from __future__ import annotations

from typing import Any

from custom_components.digitraffic_live.api import DigitrafficError, DigitrafficNotFound
from custom_components.digitraffic_live.geo import Area
from custom_components.digitraffic_live.ships import (
    ShipFeedConfig,
    VesselRegister,
    build_ship_features,
    fetch_ship_positions,
    icebreaker_mmsis,
    is_stationary,
    navigation_status_key,
    ship_heading,
    ship_type,
)
from custom_components.digitraffic_live.texts import load_texts

from .conftest import HAMINA_AREA, VESSELS, ais_locations, now_ms


def config(**overrides: Any) -> ShipFeedConfig:
    values = {
        "area": Area.from_selector(HAMINA_AREA),
        "max_age_minutes": 30,
        "ship_types": None,
        "include_moored": True,
        "icebreakers": False,
    }
    return ShipFeedConfig(**(values | overrides))


class FakeClient:
    def __init__(self, vessels: dict[int, Any] | None = None, fail: set[int] | None = None) -> None:
        self.vessels_by_mmsi = vessels or {}
        self.fail = fail or set()
        self.calls: list[tuple[str, tuple]] = []

    async def ais_locations(self, *args: Any) -> dict[str, Any]:
        self.calls.append(("ais_locations", args))
        return ais_locations()

    async def vessel(self, mmsi: int) -> dict[str, Any]:
        self.calls.append(("vessel", (mmsi,)))
        if mmsi in self.fail:
            raise DigitrafficError("boom")
        if mmsi not in self.vessels_by_mmsi:
            raise DigitrafficNotFound("unknown")
        return self.vessels_by_mmsi[mmsi]

    async def vessels(self) -> list[dict[str, Any]]:
        self.calls.append(("vessels", ()))
        return list(self.vessels_by_mmsi.values())


def test_ship_type_codes() -> None:
    assert ship_type(70) == "cargo"
    assert ship_type(84) == "tanker"
    assert ship_type(69) == "passenger"
    assert ship_type(50) == "pilot"
    assert ship_type(52) == "tug"
    assert ship_type(37) == "pleasure"
    assert ship_type(30) == "fishing"
    assert ship_type(None) == "other"


def test_movement() -> None:
    assert not is_stationary({"navStat": 0, "sog": 12, "heading": 90})
    assert is_stationary({"navStat": 0, "sog": 0.2, "heading": 90})
    assert is_stationary({"navStat": 5, "sog": 3, "heading": 90})
    assert ship_heading({"heading": 511, "cog": 278.6, "sog": 5}) == 278.6
    assert ship_heading({"heading": 511, "cog": 360, "sog": 5}) is None
    assert ship_heading({"heading": 511, "cog": 0, "sog": 0}) is None, "a still ship's course means nothing"
    assert ship_heading({"heading": 45, "cog": 0, "sog": 0}) == 45


def test_navigation_status_keys() -> None:
    assert navigation_status_key(5) == "nav_5"
    assert navigation_status_key(11) == "nav_reserved"
    assert navigation_status_key(99) == "nav_15"


def test_icebreakers_from_winter_navigation() -> None:
    data = {
        "vessels": [
            {"mmsi": 1, "activities": [{"type": "TOW", "assistedVessel": {"mmsi": 2}}]},
            {"mmsi": 2, "activities": [{"type": "WAIT"}], "plannedAssistances": [{"assistingVessel": {"mmsi": 3}}]},
            {"mmsi": 4, "activities": [{"type": "LOC"}]},
            {"mmsi": 5, "activities": [{"type": "STOP"}]},
            {"mmsi": 6, "type": "Icebreaker"},
            {"mmsi": 7, "type": "Tanker", "activities": [{"type": "WAIT"}]},
        ]
    }
    assert icebreaker_mmsis(data) == {1, 3, 4, 6}
    assert icebreaker_mmsis(None) == set()


async def test_positions_are_limited_to_the_area() -> None:
    client = FakeClient()
    positions = await fetch_ship_positions(client, config(), now_ms())
    assert [position["properties"]["mmsi"] for position in positions] == [111, 222]
    _, (since, latitude, longitude, radius) = client.calls[0]
    assert (latitude, longitude, radius) == (60.569, 27.198, 15)
    assert since < now_ms()


async def test_register_remembers_unknown_ships_but_retries_failures() -> None:
    client = FakeClient(vessels={111: VESSELS[111]}, fail={444})
    register = VesselRegister()
    await register.ensure(client, [111, 222, 444])
    assert register.get(111)["name"] == "PILOT L117"
    assert register.get(222) is None

    client.calls.clear()
    await register.ensure(client, [111, 222, 444])
    assert client.calls == [("vessel", (444,))]


async def test_register_downloads_everything_for_many_unknown_ships() -> None:
    client = FakeClient(vessels=VESSELS)
    register = VesselRegister(bulk_threshold=1)
    await register.ensure(client, [111, 222])
    assert client.calls == [("vessels", ())]
    assert register.get(222)["name"] == "KOTKA"


async def test_features_follow_the_map_feed_format() -> None:
    register = VesselRegister()
    await register.ensure(FakeClient(vessels=VESSELS), [111, 222])
    positions = await fetch_ship_positions(FakeClient(), config(), now_ms())

    features = build_ship_features(positions, register, set(), config(), load_texts("fi"))

    pilot = features[0]
    assert pilot["id"] == "ship:111"
    assert pilot["geometry"] == {"type": "Point", "coordinates": [27.17, 60.53]}
    props = pilot["properties"]
    assert props["name"] == "PILOT L117"
    assert props["kind"] == "ship.pilot"
    assert props["heading"] == 88
    assert props["stationary"] is False
    assert props["speed_kmh"] == 20.4
    assert props["footer"] == "MMSI 111 · OJ1234"
    assert props["details"] == [
        {"label": "Tyyppi", "value": "Luotsivene"},
        {"label": "Tila", "value": "Matkalla konevoimalla"},
        {"label": "Syväys", "value": 2.2, "unit": "m"},
        {"label": "Pituus × leveys", "value": "13 × 4", "unit": "m"},
    ]

    moored = features[1]["properties"]
    assert moored["stationary"] is True
    assert "heading" not in moored


async def test_filters_skip_icebreakers() -> None:
    register = VesselRegister()
    await register.ensure(FakeClient(vessels=VESSELS), [111, 222])
    positions = await fetch_ship_positions(FakeClient(), config(), now_ms())
    filtered = config(include_moored=False, ship_types=frozenset({"tanker"}))
    texts = load_texts("en")

    assert build_ship_features(positions, register, set(), filtered, texts) == []

    features = build_ship_features(positions, register, {222}, filtered, texts)
    assert [feature["properties"]["kind"] for feature in features] == ["ship.icebreaker"]
