"""Actions. The map card calls get_train_composition when a train's popup opens."""

from __future__ import annotations

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from .api import DigitrafficError, DigitrafficNotFound
from .const import ATTR_DEPARTURE_DATE, ATTR_TRAIN_NUMBER, DOMAIN, SERVICE_GET_TRAIN_COMPOSITION
from .coordinator import DigitrafficConfigEntry
from .trains import composition_details

GET_TRAIN_COMPOSITION_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEPARTURE_DATE): cv.date,
        vol.Required(ATTR_TRAIN_NUMBER): cv.positive_int,
    }
)


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    async def get_train_composition(call: ServiceCall) -> ServiceResponse:
        """A train's cars and services as map feed popup rows: {"details": [rows]}."""
        entries: list[DigitrafficConfigEntry] = hass.config_entries.async_loaded_entries(DOMAIN)
        if not entries:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="not_loaded")
        runtime = entries[0].runtime_data

        try:
            data = await runtime.client.composition(
                call.data[ATTR_DEPARTURE_DATE].isoformat(), call.data[ATTR_TRAIN_NUMBER]
            )
        except DigitrafficNotFound:
            # Many trains, e.g. most commuter trains, have no published composition.
            data = None
        except DigitrafficError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="request_failed",
                translation_placeholders={"error": str(err)},
            ) from err

        return {"details": composition_details(data, runtime.texts)}

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_TRAIN_COMPOSITION,
        get_train_composition,
        schema=GET_TRAIN_COMPOSITION_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
