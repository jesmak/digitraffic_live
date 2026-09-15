"""Digitraffic Live: live ships, trains and road traffic data from Fintraffic's Digitraffic, as map feeds.

Each feed is a config subentry with its own coordinator and sensor. The sensor
writes the Map Feed format, which the map feed plugin for ha-map-card draws.
"""

from __future__ import annotations

import asyncio

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_integration

from .api import DigitrafficClient
from .cache import DetailCache
from .const import CONF_LANGUAGE, DOMAIN
from .coordinator import COORDINATORS, DigitrafficConfigEntry, DigitrafficRuntimeData, PeriodicValue
from .services import async_setup_services
from .ships import VesselRegister, icebreaker_mmsis
from .texts import async_load_texts
from .trains import passenger_notice_index

PLATFORMS = [Platform.SENSOR]

# Icebreaker assignments and passenger notices change slowly, and every feed shares them.
ICEBREAKER_REFRESH_SECONDS = 600
PASSENGER_NOTICES_REFRESH_SECONDS = 300
# Road station lists and road sections change rarely. They're fetched only when a feed needs them.
STATION_LIST_REFRESH_SECONDS = 3600
DAILY_REFRESH_SECONDS = 24 * 3600

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    async_setup_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: DigitrafficConfigEntry) -> bool:
    integration = await async_get_integration(hass, DOMAIN)
    # Identifies the integration to Digitraffic, as its terms ask. Contains no personal information.
    client = DigitrafficClient(async_get_clientsession(hass), f"{DOMAIN}/{integration.version}")
    language = entry.data[CONF_LANGUAGE]

    async def fetch_icebreakers() -> set[int]:
        return icebreaker_mmsis(await client.winter_navigation_vessels())

    async def fetch_notices() -> dict[str, list[str]]:
        return passenger_notice_index(await client.passenger_information(), language)

    entry.runtime_data = DigitrafficRuntimeData(
        client=client,
        texts=await async_load_texts(hass, language),
        vessel_register=VesselRegister(),
        icebreakers=PeriodicValue("icebreakers", ICEBREAKER_REFRESH_SECONDS, fetch_icebreakers, set()),
        notices=PeriodicValue("passenger notices", PASSENGER_NOTICES_REFRESH_SECONDS, fetch_notices, {}),
        maintenance_tasks=PeriodicValue("maintenance tasks", DAILY_REFRESH_SECONDS, client.maintenance_tasks, []),
        forecast_sections=PeriodicValue("forecast sections", DAILY_REFRESH_SECONDS, client.forecast_sections, {}),
        weather_station_list=PeriodicValue(
            "weather stations", STATION_LIST_REFRESH_SECONDS, client.weather_stations, {}
        ),
        weather_station_details=DetailCache("weather station", client.weather_station),
        camera_list=PeriodicValue("weather cameras", STATION_LIST_REFRESH_SECONDS, client.weathercam_stations, {}),
        camera_details=DetailCache("weather camera", client.weathercam_station),
    )

    for subentry in entry.subentries.values():
        if coordinator_class := COORDINATORS.get(subentry.subentry_type):
            entry.runtime_data.coordinators[subentry.subentry_id] = coordinator_class(hass, entry, subentry)

    # A feed that fails becomes unavailable and keeps retrying; it doesn't stop the others from loading.
    await asyncio.gather(*(coordinator.async_refresh() for coordinator in entry.runtime_data.coordinators.values()))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Adding, changing or removing a feed (subentry), or changing the language, reloads everything.
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_reload_entry(hass: HomeAssistant, entry: DigitrafficConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: DigitrafficConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
