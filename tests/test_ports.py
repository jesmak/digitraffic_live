"""Ports: winter navigation's restrictions and suspensions, and the ships calling, with made-up ships and times."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.config_entries import SOURCE_USER, ConfigSubentryData
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.util import dt as dt_util
from pytest_homeassistant.common import MockConfigEntry
from pytest_homeassistant.test_util.aiohttp import AiohttpClientMocker, AiohttpClientMockResponse

from custom_components.digitraffic_live.api import MARINE_API
from custom_components.digitraffic_live.const import DOMAIN
from custom_components.digitraffic_live.ports import (
    PortConfig,
    build_port_calls,
    in_force,
    port_index,
    winter_locations,
)

NOW = "2026-02-10T12:00:00+00:00"
CONFIG = PortConfig(port="FIKTK", winter_location="FIKTK", port_calls="FIKTK", count=3)
NAMES = {"FIKTK": "Kotka", "DEHAM": "Hamburg", "EETLL": "Tallinn"}


def location(name: str, locodes: str | None, nationality: str = "FI", restrictions=(), suspensions=()) -> dict[str, Any]:
    return {
        "type": "Feature",
        "geometry": None,
        "properties": {
            "name": name,
            "type": "PORT" if locodes else "FAIRWAY",
            "locodeList": locodes,
            "nationality": nationality,
            "winterport": True,
            "restrictions": list(restrictions),
            "suspensions": list(suspensions),
        },
    }


def restriction(start: str, end: str | None, text: str) -> dict[str, Any]:
    return {"startTime": f"2026-{start}T22:00:00+00:00", "endTime": f"2026-{end}T22:00:00+00:00" if end else None, "textCompilation": text}


def suspension(start: str, end: str, due_to: str, closed: bool = False) -> dict[str, Any]:
    return {"startTime": start, "endTime": end, "prenotification": "0", "portsClosed": closed, "dueTo": due_to, "specifications": None}


# As winter navigation keeps them: last periods first, the past ones still there, fairways without a locode.
LOCATIONS = {
    "type": "FeatureCollection",
    "features": [
        location(
            "KOTKA",
            "FIKTK",
            restrictions=[
                restriction("02-14", "03-15", "IB 2000"),
                restriction("01-06", "01-31", "II 2000"),
                restriction("01-31", "02-14", "I 2000"),
            ],
            suspensions=[
                suspension("2026-02-10T08:00:00+00:00", "2026-02-10T16:00:00+00:00", "CLOSED_DUE_BAD_WEATHER", closed=True),
                suspension("2026-02-11T08:00:00+00:00", "2026-02-11T10:00:00+00:00", "CLOSED_DUE_ICE"),
            ],
        ),
        location("HAMINA", "FIHMN", restrictions=[restriction("02-06", None, "IA 4000 (2000 t)")]),
        location("LULEÅ", "SELLA", nationality="SE"),
        location("OULU DW-ROUTE", None),
    ],
}

PORTS = {
    "ssnLocations": {
        "features": [
            {"locode": locode, "properties": {"locode": locode, "locationName": name}}
            for locode, name in [*NAMES.items(), ("FIHMN", "Hamina"), ("SELLA", "Luleå"), ("FIHEL", "Helsinki")]
        ]
    },
    # Hamina has port areas of its own, but its harbours' calls are under Kotka's UN/LOCODE.
    "portAreas": {"features": [{"locode": "FIKTK", "properties": {"portAreaName": "Mussalo"}}, {"locode": "FIHEL"}, {"locode": "FIHMN"}]},
    "berths": {"berths": []},
}


def call(call_id: int, vessel: str, area: dict[str, Any], prev_port: str = "DEHAM", next_port: str = "EETLL", type_code: int = 70) -> dict:
    return {
        "portCallId": call_id,
        "vesselName": vessel,
        "vesselTypeCode": type_code,
        "prevPort": prev_port,
        "nextPort": next_port,
        "portAreaDetails": [
            {"berthCode": "C1", "portAreaName": "MUSSALO (KONTTI)", "eta": None, "ata": None, "etd": None, "atd": None} | area
        ],
    }


def at(time: str) -> str:
    return f"2026-02-10T{time}:00+00:00"


def calls(*items: dict) -> bytes:
    return json.dumps({"dataUpdatedTime": NOW, "portCalls": list(items)}).encode()


def build(raw: bytes, arrivals: bool, config: PortConfig = CONFIG) -> list[dict]:
    return build_port_calls(raw, config, NAMES, arrivals, datetime.fromisoformat(NOW))


def test_winter_navigation_is_read_by_locode_with_its_periods_in_order() -> None:
    locations = winter_locations(LOCATIONS)

    assert set(locations) == {"FIKTK", "FIHMN", "SELLA"}, "a fairway has no locode, so it is no port"
    kotka = locations["FIKTK"]
    assert [period.text for period in kotka.restrictions] == ["II 2000", "I 2000", "IB 2000"]
    assert [period.text for period in kotka.suspensions] == ["bad_weather", "ice"], "a reason not seen before keeps its code"
    assert locations["FIHMN"].restrictions[0].end is None
    assert locations["FIHMN"].restrictions[0].covers(dt_util.parse_datetime("2027-01-01T00:00:00+00:00")), "open-ended"


def test_a_location_with_several_locodes_is_each_of_them() -> None:
    locations = winter_locations({"features": [location("TWIN", "FIAAA, FIBBB")]})

    assert locations["FIAAA"] is locations["FIBBB"]


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        ("2026-01-31T21:59:59+00:00", "II 2000"),
        ("2026-01-31T22:00:00+00:00", "I 2000"),
        ("2026-03-15T21:59:59+00:00", "IB 2000"),
        ("2026-03-15T22:00:00+00:00", None),
        ("2026-01-06T21:59:59+00:00", None),
    ],
)
def test_a_period_is_in_force_from_its_start_until_its_end(now: str, expected: str | None) -> None:
    kotka = winter_locations(LOCATIONS)["FIKTK"]

    current = in_force(kotka.restrictions, datetime.fromisoformat(now))

    assert (current.text if current else None) == expected


def test_a_suspension_says_whether_it_closes_the_port() -> None:
    kotka = winter_locations(LOCATIONS)["FIKTK"]

    assert [period.closed for period in kotka.suspensions] == [True, False]


def test_the_port_list_gives_names_and_the_ports_with_calls() -> None:
    index = port_index(json.dumps(PORTS).encode())

    assert index.names["FIHMN"] == "Hamina"
    assert index.call_ports == {"FIKTK", "FIHEL", "FIHMN"}


def test_a_ships_arrival_from_the_port_it_comes_from() -> None:
    [arrival] = build(calls(call(1, "Example Star", {"eta": at("14:00")})), arrivals=True)

    assert arrival == {
        "id": "call-arrival:1",
        "line": "",
        "mode": "ship",
        "headsign": "Example Star · Hamburg",
        "scheduled": at("14:00"),
        "estimated": at("14:00"),
        "realtime": False,
        "delay": 0,
        "platform": "C1",
        "harbour": "MUSSALO (KONTTI)",
    }


def test_a_ship_that_has_come_in_is_arrived_at_its_actual_time() -> None:
    [arrival] = build(calls(call(1, "Example Star", {"eta": at("11:00"), "ata": at("11:40")})), arrivals=True)

    assert (arrival["estimated"], arrival["arrived"], arrival["realtime"], arrival["delay"]) == (at("11:40"), True, True, 2400)


def test_a_ferry_leaves_for_its_next_port_from_a_named_berth_only() -> None:
    raw = calls(call(1, "Example Ferry", {"etd": at("13:00"), "berthCode": "MUU", "portAreaName": "Ei tiedossa"}, type_code=20))

    [departure] = build(raw, arrivals=False)

    assert (departure["mode"], departure["headsign"]) == ("ferry", "Example Ferry · Tallinn")
    assert "platform" not in departure and "harbour" not in departure, "MUU and Ei tiedossa are no names"


def test_a_next_port_that_is_the_port_itself_is_left_out() -> None:
    [departure] = build(calls(call(1, "Example Star", {"etd": at("13:00")}, next_port="FIKTK")), arrivals=False)

    assert departure["headsign"] == "Example Star"


def test_a_port_without_a_name_is_shown_by_its_locode() -> None:
    [departure] = build(calls(call(1, "Example Star", {"etd": at("13:00")}, next_port="NLRTM")), arrivals=False)

    assert departure["headsign"] == "Example Star · NLRTM"


def test_departures_are_listed_until_a_minute_past_and_counted() -> None:
    raw = calls(
        call(1, "Gone", {"etd": at("10:00"), "atd": at("11:58")}),
        call(2, "Leaving now", {"etd": "2026-02-10T11:59:30+00:00"}),
        call(3, "Third", {"etd": at("15:00")}),
        call(4, "Second", {"etd": at("13:00")}),
        call(5, "Fourth", {"etd": at("16:00")}),
        call(6, "No time", {}),
    )

    departures = build(raw, arrivals=False)

    assert [departure["headsign"].split(" · ")[0] for departure in departures] == ["Leaving now", "Second", "Third"]


def test_arrivals_keep_the_latest_two_that_came_in_besides_the_count() -> None:
    raw = calls(
        call(1, "Long ago", {"eta": at("10:00"), "ata": at("11:20")}),
        call(2, "In earlier", {"eta": at("11:30"), "ata": at("11:35")}),
        call(3, "In just now", {"eta": at("11:50"), "ata": at("11:55")}),
        call(4, "In first", {"eta": at("11:00"), "ata": at("11:45")}),
        call(5, "Late, no word", {"eta": at("11:00")}),
        call(6, "Next", {"eta": at("13:00")}),
        call(7, "After", {"eta": at("14:00")}),
    )

    arrivals = build(raw, arrivals=True, config=PortConfig("FIKTK", None, "FIKTK", count=2))

    # Over half an hour past its announced time, a ship with no word of its arrival is no longer listed.
    assert [arrival["headsign"].split(" · ")[0] for arrival in arrivals] == ["In first", "In just now", "Next", "After"]


def test_calls_that_are_no_list_are_an_error() -> None:
    with pytest.raises(ValueError):
        build(b'{"message": "Internal error"}', arrivals=True)


# ---------------- in Home Assistant ----------------


def mock_api(aioclient_mock: AiohttpClientMocker, arriving: bytes, departing: bytes) -> None:
    aioclient_mock.get(f"{MARINE_API}/winter-navigation/v2/locations", json=LOCATIONS)
    aioclient_mock.get(f"{MARINE_API}/port-call/v1/ports", json=PORTS)

    async def port_calls(method, url, data):
        assert url.query["locode"] == "FIKTK"
        body = arriving if "etaFrom" in url.query else departing
        return AiohttpClientMockResponse(method, url, text=body.decode())

    aioclient_mock.get(f"{MARINE_API}/port-call/v1/port-calls", side_effect=port_calls)


def port_entry(hass: HomeAssistant, **data: Any) -> MockConfigEntry:
    title = {"FIKTK": "Kotka", "SELLA": "Luleå"}[data["port"]]
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Digitraffic",
        data={"language": "en"},
        subentries_data=[ConfigSubentryData(subentry_type="port", title=title, unique_id=data["port"], data=data)],
    )
    entry.add_to_hass(hass)
    return entry


async def test_a_port_has_its_restriction_suspension_and_ships(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, freezer: FrozenDateTimeFactory
) -> None:
    freezer.move_to(NOW)
    mock_api(aioclient_mock, calls(call(1, "Example Star", {"eta": at("14:00")})), calls(call(2, "Example Ferry", {"etd": at("13:00")})))
    entry = port_entry(hass, port="FIKTK", winter_location="FIKTK", port_calls="FIKTK", departures=5)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    restriction = hass.states.get("sensor.kotka_traffic_restriction")
    assert restriction.state == "restricted"
    assert restriction.attributes["restriction"] == "I 2000"
    assert [period["restriction"] for period in restriction.attributes["restrictions"]] == ["II 2000", "I 2000", "IB 2000"]
    suspension = hass.states.get("binary_sensor.kotka_suspension")
    assert suspension.state == "on"
    assert (suspension.attributes["reason"], suspension.attributes["port_closed"]) == ("bad_weather", True)
    assert [period["port_closed"] for period in suspension.attributes["suspensions"]] == [True, False]
    departures = hass.states.get("sensor.kotka_departures")
    assert departures.state == at("13:00")
    assert (departures.attributes["stop_id"], departures.attributes["stop_name"], departures.attributes["direction"]) == (
        "FIKTK",
        "Kotka",
        "departures",
    )
    arrivals = hass.states.get("sensor.kotka_arrivals")
    assert [arrival["headsign"] for arrival in arrivals.attributes["departures"]] == ["Example Star · Hamburg"]
    query = next(url.query for _method, url, _data, _headers in aioclient_mock.mock_calls if "etaFrom" in url.query)
    assert (query["etaFrom"], query["etaTo"]) == ("2026-02-10T00:00:00Z", "2026-02-17T12:00:00Z")


async def test_a_port_followed_for_winter_navigation_only_asks_for_no_ships(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, freezer: FrozenDateTimeFactory
) -> None:
    freezer.move_to("2026-03-20T12:00:00+00:00")
    mock_api(aioclient_mock, calls(), calls())
    entry = port_entry(hass, port="SELLA", winter_location="SELLA")

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.lulea_traffic_restriction").state == "none"
    assert hass.states.get("binary_sensor.lulea_suspension").state == "off"
    assert hass.states.get("sensor.lulea_departures") is None
    assert not any("port-call" in url.path for _method, url, _data, _headers in aioclient_mock.mock_calls), "nor the port list"


# ---------------- the flow ----------------


async def setup_entry(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> MockConfigEntry:
    mock_api(aioclient_mock, calls(), calls())
    entry = MockConfigEntry(domain=DOMAIN, title="Digitraffic", data={"language": "en"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_the_ports_on_offer_are_winter_navigations_and_those_with_calls(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    entry = await setup_entry(hass, aioclient_mock)

    result = await hass.config_entries.subentries.async_init((entry.entry_id, "port"), context={"source": SOURCE_USER})

    options = result["data_schema"].schema["port"].config["options"]
    assert [option["label"] for option in options] == ["Hamina (FIHMN)", "Helsinki (FIHEL)", "Kotka (FIKTK)", "Luleå (SELLA)"]


async def test_a_finnish_port_reads_its_own_locode_by_default_and_can_read_a_neighbours(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    entry = await setup_entry(hass, aioclient_mock)
    result = await hass.config_entries.subentries.async_init((entry.entry_id, "port"), context={"source": SOURCE_USER})

    result = await hass.config_entries.subentries.async_configure(result["flow_id"], {"port": "FIHMN"})

    assert result["step_id"] == "port"
    suggested = {str(key): key.description["suggested_value"] for key in result["data_schema"].schema if key.description}
    assert suggested == {"winter_location": "FIHMN", "port_calls": "FIHMN", "departures": 5}
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], {"departures": 5})
    assert result["errors"] == {"base": "nothing_followed"}
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"winter_location": "FIHMN", "port_calls": "FIKTK", "departures": 4}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    [subentry] = entry.subentries.values()
    assert (subentry.title, subentry.unique_id) == ("Hamina", "FIHMN")
    assert subentry.data == {"port": "FIHMN", "winter_location": "FIHMN", "port_calls": "FIKTK", "departures": 4}


async def test_a_foreign_port_is_added_straight_away_and_only_once(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    entry = await setup_entry(hass, aioclient_mock)
    result = await hass.config_entries.subentries.async_init((entry.entry_id, "port"), context={"source": SOURCE_USER})

    result = await hass.config_entries.subentries.async_configure(result["flow_id"], {"port": "SELLA"})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert result["data"] == {"port": "SELLA", "winter_location": "SELLA"}

    result = await hass.config_entries.subentries.async_init((entry.entry_id, "port"), context={"source": SOURCE_USER})
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], {"port": "SELLA"})
    assert result["reason"] == "already_configured"


async def test_changing_a_foreign_port_offers_no_ships(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    mock_api(aioclient_mock, calls(), calls())
    entry = port_entry(hass, port="SELLA", winter_location="SELLA")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    [subentry_id] = entry.subentries

    result = await entry.start_subentry_reconfigure_flow(hass, subentry_id)

    assert [str(key) for key in result["data_schema"].schema] == ["winter_location"]
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], {})
    assert result["errors"] == {"base": "nothing_followed"}


async def test_changing_a_finnish_port_keeps_its_choices_and_count(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    mock_api(aioclient_mock, calls(), calls())
    entry = port_entry(hass, port="FIKTK", winter_location="FIKTK", port_calls="FIKTK", departures=3)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    [subentry_id] = entry.subentries

    result = await entry.start_subentry_reconfigure_flow(hass, subentry_id)
    suggested = {str(key): key.description["suggested_value"] for key in result["data_schema"].schema if key.description}
    assert suggested == {"winter_location": "FIKTK", "port_calls": "FIKTK", "departures": 3}

    result = await hass.config_entries.subentries.async_configure(result["flow_id"], {"port_calls": "FIKTK", "departures": 7})
    assert result["reason"] == "reconfigure_successful"
    await hass.async_block_till_done()
    assert entry.subentries[subentry_id].data == {"port": "FIKTK", "port_calls": "FIKTK", "departures": 7}
