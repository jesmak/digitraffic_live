"""Setting up feeds, the sensors they create, and the composition action."""

from __future__ import annotations

from dataclasses import replace

from homeassistant.config_entries import ConfigEntryState, ConfigSubentryData
from homeassistant.const import MATCH_ALL, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.digitraffic_live.api import MARINE_API, RAILWAY_API
from custom_components.digitraffic_live.const import DOMAIN
from custom_components.digitraffic_live.coordinator import WeatherCameraCoordinator
from custom_components.digitraffic_live.sensor import MapFeedSensor

from .conftest import HAMINA_AREA, ROAD_AREA, VESSELS, ais_locations


def feed_entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Digitraffic",
        data={"language": "en"},
        subentries_data=[
            ConfigSubentryData(
                subentry_type="ships",
                title="Ships near the cabin",
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


async def test_feeds_create_map_feed_sensors(hass: HomeAssistant, digitraffic_api: AiohttpClientMocker) -> None:
    entry = feed_entry(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    ships = hass.states.get("sensor.ships_near_the_cabin")
    assert ships.state == "2"
    assert ships.attributes["map_feed_version"] == 1
    assert ships.attributes["attribution"] == "Fintraffic / digitraffic.fi, CC BY 4.0"
    assert ships.attributes["area"] == {"center": [60.569, 27.198], "radius_km": 15.0}
    geojson = ships.attributes["geojson"]
    assert geojson["type"] == "FeatureCollection"
    assert [feature["id"] for feature in geojson["features"]] == ["ship:111", "ship:222"]

    trains = hass.states.get("sensor.trains_hki_lr")
    assert trains.state == "1"
    assert "area" not in trains.attributes
    assert trains.attributes["geojson"]["features"][0]["properties"]["notices"] == ["Delayed by track works."]

    for _method, _url, _data, headers in digitraffic_api.mock_calls:
        assert headers["Digitraffic-User"].startswith("digitraffic_live/")

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_devices_without_a_subentry_are_removed(
    hass: HomeAssistant, digitraffic_api: AiohttpClientMocker
) -> None:
    entry = feed_entry(hass)
    device_registry = dr.async_get(hass)
    stale = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={(DOMAIN, "weather_station_3036")}
    )
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert device_registry.async_get(stale.id) is None
    devices = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    assert {identifier for device in devices for _, identifier in device.identifiers} == set(entry.subentries)


async def test_feeds_are_kept_out_of_the_recorder() -> None:
    assert MATCH_ALL in MapFeedSensor._unrecorded_attributes


async def test_a_failing_feed_does_not_affect_the_others(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
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
    assert hass.states.get("sensor.ships_near_the_cabin").state == "2"


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

    assert hass.states.get("sensor.maintenance").state == "2"
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
    assert hass.states.get("sensor.road_6_lappeenranta_karki_road_weather_warning").state == "ok"

    # Each view of a weather camera is an image entity; its state is when the picture was taken.
    view = "image.road_6_lappeenranta_saimaa_channel_imatralle"
    assert hass.states.get(view).state == "2026-09-15T11:47:33+00:00"
    assert hass.states.get("image.road_6_lappeenranta_saimaa_channel_tienpinta") is not None

    camera = next(
        coordinator
        for coordinator in entry.runtime_data.coordinators.values()
        if isinstance(coordinator, WeatherCameraCoordinator)
    )
    image = hass.data["image"].get_entity(view)
    image._cached_image = object()
    camera.async_set_updated_data(replace(camera.data, picture_times={"C0355801": "2026-09-15T11:57:33Z"}))
    await hass.async_block_till_done()
    assert hass.states.get(view).state == "2026-09-15T11:57:33+00:00"
    assert image._cached_image is None, "a new picture replaces the cached one"
    assert hass.states.get("image.road_6_lappeenranta_saimaa_channel_tienpinta").state == STATE_UNAVAILABLE
