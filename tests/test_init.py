"""Setting up feeds, the sensors they create, and the composition action."""

from __future__ import annotations

from dataclasses import replace
from types import MappingProxyType

import pytest
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.config_entries import ConfigEntryState, ConfigSubentry, ConfigSubentryData
from homeassistant.const import MATCH_ALL, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.digitraffic_live import sensor
from custom_components.digitraffic_live.api import MARINE_API, RAILWAY_API
from custom_components.digitraffic_live.const import DOMAIN
from custom_components.digitraffic_live.coordinator import WeatherCameraCoordinator, WeatherStationCoordinator
from custom_components.digitraffic_live.sensor import MapFeedSensor, StationSensor

from .conftest import HAMINA_AREA, ROAD_AREA, VESSELS, ais_locations


def feed_entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Digitraffic",
        data={"language": "en"},
        subentries_data=[
            ConfigSubentryData(
                subentry_type="ships",
                title="Ships near the harbour",
                unique_id=None,
                data={
                    "area": HAMINA_AREA,
                    "include_moored": True,
                    "icebreakers": True,
                    "max_age_minutes": 30,
                    "refresh_seconds": 60,
                },
            ),
            ConfigSubentryData(
                subentry_type="trains",
                title="Trains HKI–LR",
                unique_id=None,
                data={"route": ["HKI", "LR"], "use_area": False, "max_age_minutes": 15, "refresh_seconds": 60},
            ),
        ],
    )
    entry.add_to_hass(hass)
    return entry


@pytest.mark.parametrize("change", ["data", "subentry"])
async def test_a_change_saved_while_setting_up_is_applied(
    hass: HomeAssistant, digitraffic_api: AiohttpClientMocker, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, title="Digitraffic", data={"language": "en"})
    entry.add_to_hass(hass)
    trains = ConfigSubentry(
        data=MappingProxyType({"route": ["HKI", "LR"], "use_area": False, "max_age_minutes": 15, "refresh_seconds": 60}),
        subentry_type="trains",
        title="Trains HKI–LR",
        unique_id=None,
    )
    forward = hass.config_entries.async_forward_entry_setups
    setups = []

    async def save_while_setting_up(entry: MockConfigEntry, platforms) -> None:
        # Saved as a flow would save it, before setup has added its update listener.
        if not setups:
            if change == "data":
                hass.config_entries.async_update_entry(entry, data={"language": "fi"})
            else:
                hass.config_entries.async_add_subentry(entry, trains)
        setups.append(entry.runtime_data)
        await forward(entry, platforms)

    monkeypatch.setattr(hass.config_entries, "async_forward_entry_setups", save_while_setting_up)
    # Not asserted: the reload may already be under way when the setup returns.
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert len(setups) == 2, "set up again with the change"
    if change == "data":
        assert entry.runtime_data.texts.language == "fi"
    else:
        assert trains.subentry_id in entry.runtime_data.coordinators


async def test_an_entry_left_on_swedish_is_switched_to_english(hass: HomeAssistant, digitraffic_api: AiohttpClientMocker) -> None:
    entry = MockConfigEntry(domain=DOMAIN, title="Digitraffic", data={"language": "sv"}, version=1, minor_version=1)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.data["language"] == "en"
    assert entry.minor_version == 2


async def test_feeds_create_map_feed_sensors(hass: HomeAssistant, digitraffic_api: AiohttpClientMocker) -> None:
    entry = feed_entry(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    ships = hass.states.get("sensor.ships_near_the_harbour")
    assert ships.state == "2"
    assert ships.attributes["map_feed_version"] == 1
    assert ships.attributes["attribution"] == "Fintraffic / digitraffic.fi, CC BY 4.0"
    assert ships.attributes["area"] == {"center": [60.569, 27.198], "radius_km": 15.0}
    assert ships.attributes["feed_type"] == "ship"
    assert "list" not in ships.attributes, "only trains offer orders of their own"
    geojson = ships.attributes["geojson"]
    assert geojson["type"] == "FeatureCollection"
    assert [feature["id"] for feature in geojson["features"]] == ["ship:111", "ship:222"]

    trains = hass.states.get("sensor.trains_hki_lr")
    assert trains.state == "1"
    assert "area" not in trains.attributes
    assert trains.attributes["feed_type"] == "train"
    assert trains.attributes["list"] == {
        "sort": [
            {"key": "delay", "label": "Delay", "property": "delay_minutes", "order": "desc"},
            {"key": "number", "label": "Number", "property": "badge"},
        ],
        "default": "delay",
        "count": "trains",
        "count_one": "train",
    }
    assert trains.attributes["geojson"]["features"][0]["properties"]["notices"] == ["Delayed by track works."]

    for _method, _url, _data, headers in digitraffic_api.mock_calls:
        assert headers["Digitraffic-User"].startswith("digitraffic_live/")

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_devices_without_a_subentry_are_removed(hass: HomeAssistant, digitraffic_api: AiohttpClientMocker) -> None:
    entry = feed_entry(hass)
    device_registry = dr.async_get(hass)
    stale = device_registry.async_get_or_create(config_entry_id=entry.entry_id, identifiers={(DOMAIN, "weather_station_3036")})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert device_registry.async_get(stale.id) is None
    devices = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    assert {identifier for device in devices for _, identifier in device.identifiers} == set(entry.subentries)


async def test_feeds_are_kept_out_of_the_recorder() -> None:
    assert MATCH_ALL in MapFeedSensor._unrecorded_attributes


async def test_a_failing_feed_does_not_affect_the_others(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    aioclient_mock.get(f"{MARINE_API}/ais/v1/locations", json=ais_locations())
    for mmsi, vessel in VESSELS.items():
        aioclient_mock.get(f"{MARINE_API}/ais/v1/vessels/{mmsi}", json=vessel)
    aioclient_mock.get(f"{MARINE_API}/winter-navigation/v2/vessels", json={"vessels": []})
    aioclient_mock.post(f"{RAILWAY_API}/v2/graphql/graphql", status=500)

    entry = feed_entry(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert hass.states.get("sensor.trains_hki_lr").state == STATE_UNAVAILABLE
    assert hass.states.get("sensor.ships_near_the_harbour").state == "2"


async def test_train_composition_action(hass: HomeAssistant, digitraffic_api: AiohttpClientMocker) -> None:
    entry = feed_entry(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    response = await hass.services.async_call(
        DOMAIN,
        "get_train_composition",
        {"departure_date": "2026-09-14", "train_number": 8},
        blocking=True,
        return_response=True,
    )
    assert response == {"details": [{"label": "Train", "value": "5 cars · max 200 km/h · restaurant, pets"}]}

    response = await hass.services.async_call(
        DOMAIN,
        "get_train_composition",
        {"departure_date": "2026-09-14", "train_number": 9},
        blocking=True,
        return_response=True,
    )
    assert response == {"details": []}


async def test_road_feeds_create_sensors(hass: HomeAssistant, road_api: AiohttpClientMocker) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Digitraffic",
        data={"language": "en"},
        subentries_data=[
            ConfigSubentryData(
                subentry_type="traffic_messages",
                title="Road works",
                unique_id=None,
                data={"area": ROAD_AREA, "message_types": [], "upcoming_days": 7, "refresh_seconds": 300},
            ),
            ConfigSubentryData(
                subentry_type="road_maintenance",
                title="Maintenance",
                unique_id=None,
                data={
                    "area": ROAD_AREA,
                    "max_age_minutes": 60,
                    "show_routes": True,
                    "route_hours": 2,
                    "refresh_seconds": 60,
                },
            ),
            ConfigSubentryData(
                subentry_type="road_conditions",
                title="Road conditions",
                unique_id=None,
                data={"area": ROAD_AREA, "forecast": "2h", "only_poor": False, "refresh_seconds": 600},
            ),
            ConfigSubentryData(
                subentry_type="weather_stations",
                title="Road weather",
                unique_id=None,
                data={"area": ROAD_AREA, "refresh_seconds": 300},
            ),
            ConfigSubentryData(
                subentry_type="weather_cameras",
                title="Road cameras",
                unique_id=None,
                data={"area": ROAD_AREA, "refresh_seconds": 600},
            ),
            ConfigSubentryData(
                subentry_type="road_weather_station",
                title="Road 6 Lappeenranta, Kärki",
                unique_id="3036",
                data={"station": "3036", "refresh_seconds": 300},
            ),
            ConfigSubentryData(
                subentry_type="weather_camera",
                title="Road 6 Lappeenranta, Saimaa channel",
                unique_id="C03558",
                data={"camera": "C03558", "refresh_seconds": 600},
            ),
        ],
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    road_works = hass.states.get("sensor.road_works")
    assert road_works.state == "4"
    assert road_works.attributes["icon"] == "mdi:alert"
    kinds = {feature["properties"]["kind"] for feature in road_works.attributes["geojson"]["features"]}
    assert {"road.roadwork", "road.accident", "road.exempted_transport"} <= kinds

    assert road_works.attributes["feed_type"] == "road"
    maintenance = hass.states.get("sensor.maintenance")
    assert maintenance.state == "2"
    assert maintenance.attributes["icon"] == "mdi:truck-snowflake"
    conditions = hass.states.get("sensor.road_conditions")
    assert conditions.state == "1", "the state counts sections with poor conditions"
    assert len(conditions.attributes["geojson"]["features"]) == 2
    assert hass.states.get("sensor.road_weather").state == "1"
    cameras = hass.states.get("sensor.road_cameras")
    assert cameras.state == "1"
    assert len(cameras.attributes["geojson"]["features"][0]["properties"]["images"]) == 3

    # A road weather station is a device with its own sensors.
    road_temperature = hass.states.get("sensor.road_6_lappeenranta_karki_road_temperature")
    assert road_temperature.state == "22.9"
    assert road_temperature.attributes["unit_of_measurement"] == "°C"
    assert hass.states.get("sensor.road_6_lappeenranta_karki_air_temperature").state == "14.6"
    assert hass.states.get("sensor.road_6_lappeenranta_karki_road_surface").state == "dry"
    assert hass.states.get("sensor.road_6_lappeenranta_karki_grip").state == "0.82"
    assert hass.states.get("sensor.road_6_lappeenranta_karki_grip_condition").state == "good"
    assert hass.states.get("sensor.road_6_lappeenranta_karki_wind_speed").state == "1.5"
    assert hass.states.get("sensor.road_6_lappeenranta_karki_precipitation").state == "none"
    assert hass.states.get("sensor.road_6_lappeenranta_karki_precipitation_type").state == "none"
    assert hass.states.get("sensor.road_6_lappeenranta_karki_visibility").state == "20.0"
    assert hass.states.get("sensor.road_6_lappeenranta_karki_road_weather_warning").state == "ok"

    # Each view of a weather camera is an image entity; its state is when the picture was taken.
    view = "image.road_6_lappeenranta_saimaa_channel_imatralle"
    assert hass.states.get(view).state == "2026-09-15T11:47:33+00:00"
    assert hass.states.get("image.road_6_lappeenranta_saimaa_channel_tienpinta") is not None

    camera = next(
        coordinator for coordinator in entry.runtime_data.coordinators.values() if isinstance(coordinator, WeatherCameraCoordinator)
    )
    image = hass.data["image"].get_entity(view)
    image._cached_image = object()
    camera.async_set_updated_data(replace(camera.data, picture_times={"C0355801": "2026-09-15T11:57:33Z"}))
    await hass.async_block_till_done()
    assert hass.states.get(view).state == "2026-09-15T11:57:33+00:00"
    assert image._cached_image is None, "a new picture replaces the cached one"
    assert hass.states.get("image.road_6_lappeenranta_saimaa_channel_tienpinta").state == STATE_UNAVAILABLE


STATION_KEYS_ADDED = {"air_temperature", "road_temperature", "wind_speed", "visibility", "road_surface", "grip", "grip_condition"}


async def test_a_station_gets_sensors_only_for_what_it_reports(
    hass: HomeAssistant, road_api: AiohttpClientMocker, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Station 5007's first fetch fails, so it starts with nothing. Its sensors appear as it reports them, each one
    # created once, and a reload starts over.
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Digitraffic",
        data={"language": "en"},
        subentries_data=[
            ConfigSubentryData(
                subentry_type="road_weather_station",
                title="Road 13 Example",
                unique_id="5007",
                data={"station": "5007", "refresh_seconds": 300},
            ),
        ],
    )
    entry.add_to_hass(hass)
    created: list[str] = []

    def count(coordinator: WeatherStationCoordinator, description: SensorEntityDescription) -> StationSensor:
        created.append(description.key)
        return StationSensor(coordinator, description)

    monkeypatch.setattr(sensor, "StationSensor", count)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    entity_registry = er.async_get(hass)

    def station_entities() -> set[str]:
        return {entity.translation_key for entity in er.async_entries_for_config_entry(entity_registry, entry.entry_id)}

    assert station_entities() == set()

    [coordinator] = entry.runtime_data.coordinators.values()
    assert isinstance(coordinator, WeatherStationCoordinator)
    readings = {"ILMA": 3.1, "TIEN_LÄMPÖTILA_DST-ANT": 1.2, "KESKITUULI": 4.0, "NÄKYVYYS_M": 900}
    coordinator.async_set_updated_data({name: {"name": name, "value": value} for name, value in readings.items()})
    await hass.async_block_till_done()
    assert station_entities() == {"air_temperature", "road_temperature", "wind_speed", "visibility"}
    assert hass.states.get("sensor.road_13_example_visibility").state == "0.9"

    # A sensor reporting a fault code still gets its entity, and a sensor that drops out keeps its entity.
    coordinator.async_set_updated_data({"KELI_1": {"name": "KELI_1", "value": 0}, "KITKA1": {"name": "KITKA1", "value": 0.31}})
    await hass.async_block_till_done()
    assert station_entities() == STATION_KEYS_ADDED
    assert hass.states.get("sensor.road_13_example_road_surface").state == "unknown"
    assert hass.states.get("sensor.road_13_example_grip_condition").state == "fair"
    assert hass.states.get("sensor.road_13_example_air_temperature").state == "unknown"

    # Each sensor is created once, also when the station reports it again.
    coordinator.async_set_updated_data({name: {"name": name, "value": value} for name, value in readings.items()})
    await hass.async_block_till_done()
    assert sorted(created) == sorted(STATION_KEYS_ADDED)
    assert hass.states.get("sensor.road_13_example_air_temperature").state == "3.1"

    # A reload starts over: the old coordinator is left with no listeners, and a sensor is created again only once
    # the station reports it.
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert not coordinator._listeners
    [coordinator] = entry.runtime_data.coordinators.values()
    del created[:]
    coordinator.async_set_updated_data({"ILMA": {"name": "ILMA", "value": 2.5}})
    await hass.async_block_till_done()
    assert created == ["air_temperature"]
    assert hass.states.get("sensor.road_13_example_air_temperature").state == "2.5"
    grip = hass.states.get("sensor.road_13_example_grip")
    assert grip.state == STATE_UNAVAILABLE
    assert grip.attributes["restored"] is True
    assert station_entities() == STATION_KEYS_ADDED
