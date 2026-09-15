"""The config flow and the feed subentry flows."""

from __future__ import annotations

from homeassistant.config_entries import SOURCE_RECONFIGURE, SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.digitraffic_live.const import DOMAIN

from .conftest import HAMINA_AREA, ROAD_AREA

SHIP_FEED = {
    "name": "Ships near the cabin",
    "area": HAMINA_AREA,
    "ship_types": [],
    "include_moored": True,
    "icebreakers": True,
    "max_age_minutes": 30,
    "refresh_seconds": 60,
}

TRAIN_FEED = {
    "name": "Trains HKI–LR",
    "route": ["HKI", "LR"],
    "categories": [],
    "use_area": False,
    "area": HAMINA_AREA,
    "max_age_minutes": 15,
    "refresh_seconds": 60,
}


async def setup_entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, title="Digitraffic", data={"language": "en"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_user_flow_creates_the_entry(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"language": "fi"})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {"language": "fi"}


async def test_only_one_entry_is_allowed(hass: HomeAssistant) -> None:
    await setup_entry(hass)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_adding_a_ship_feed_creates_its_sensor(hass: HomeAssistant, digitraffic_api: AiohttpClientMocker) -> None:
    entry = await setup_entry(hass)

    result = await hass.config_entries.subentries.async_init((entry.entry_id, "ships"), context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.subentries.async_configure(result["flow_id"], SHIP_FEED)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    subentry = next(iter(entry.subentries.values()))
    assert subentry.title == "Ships near the cabin"
    assert subentry.data["area"] == HAMINA_AREA
    assert "name" not in subentry.data

    state = hass.states.get("sensor.ships_near_the_cabin")
    assert state is not None
    assert state.state == "2"


async def test_ship_feed_needs_a_radius(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass)
    result = await hass.config_entries.subentries.async_init((entry.entry_id, "ships"), context={"source": SOURCE_USER})
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], SHIP_FEED | {"area": {"latitude": 60.4, "longitude": 27.3}}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"area": "area_radius"}


async def test_train_feed_validation_and_creation(hass: HomeAssistant, digitraffic_api: AiohttpClientMocker) -> None:
    entry = await setup_entry(hass)
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "trains"), context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    route_options = result["data_schema"].schema["route"].config["options"]
    assert [option["value"] for option in route_options] == ["HKI", "LR"]

    result = await hass.config_entries.subentries.async_configure(result["flow_id"], TRAIN_FEED | {"route": ["HKI"]})
    assert result["errors"] == {"route": "route_too_short"}

    result = await hass.config_entries.subentries.async_configure(result["flow_id"], TRAIN_FEED | {"route": []})
    assert result["errors"] == {"base": "route_or_area"}

    result = await hass.config_entries.subentries.async_configure(result["flow_id"], TRAIN_FEED)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    subentry = next(iter(entry.subentries.values()))
    assert subentry.data["route"] == ["HKI", "LR"]
    assert "area" not in subentry.data, "the area is dropped when it's not in use"
    assert hass.states.get("sensor.trains_hki_lr").state == "1"


async def test_reconfiguring_a_feed(hass: HomeAssistant, digitraffic_api: AiohttpClientMocker) -> None:
    entry = await setup_entry(hass)
    result = await hass.config_entries.subentries.async_init((entry.entry_id, "ships"), context={"source": SOURCE_USER})
    await hass.config_entries.subentries.async_configure(result["flow_id"], SHIP_FEED)
    await hass.async_block_till_done()
    subentry_id = next(iter(entry.subentries))

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "ships"), context={"source": SOURCE_RECONFIGURE, "subentry_id": subentry_id}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], SHIP_FEED | {"name": "Cabin ships", "include_moored": False}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    await hass.async_block_till_done()

    subentry = entry.subentries[subentry_id]
    assert subentry.title == "Cabin ships"
    assert subentry.data["include_moored"] is False
    assert hass.states.get("sensor.ships_near_the_cabin").state == "1", "the moored ship is left out after reload"


async def test_station_list_failure_aborts(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    entry = await setup_entry(hass)
    aioclient_mock.get("https://rata.digitraffic.fi/api/v1/metadata/stations", status=500)
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "trains"), context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"


async def test_adding_a_traffic_message_feed(hass: HomeAssistant, road_api: AiohttpClientMocker) -> None:
    entry = await setup_entry(hass)

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "traffic_messages"), context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            "name": "Road works",
            "area": ROAD_AREA,
            "message_types": ["road_works"],
            "upcoming_days": 3.0,
            "refresh_seconds": 300.0,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    subentry = next(iter(entry.subentries.values()))
    assert subentry.data["upcoming_days"] == 3
    assert subentry.data["message_types"] == ["road_works"]
    assert hass.states.get("sensor.road_works").state == "2"


async def test_road_feeds_need_a_radius(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass)
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "weather_cameras"), context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"name": "Cameras", "area": {**ROAD_AREA, "radius": 0}, "refresh_seconds": 600}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"area": "area_radius"}
