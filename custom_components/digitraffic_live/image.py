"""Image entities for the views of a road weather camera.

A weather camera subentry is a device with an image entity for each view. The
picture is downloaded by Home Assistant when it's shown, and again whenever
Digitraffic reports that a new picture has been taken.
"""

from __future__ import annotations

from homeassistant.components.image import ImageEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import ATTRIBUTION, DOMAIN
from .coordinator import DigitrafficConfigEntry, WeatherCameraCoordinator
from .weather_cameras import IMAGE_URL


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DigitrafficConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    for subentry_id, coordinator in entry.runtime_data.coordinators.items():
        if isinstance(coordinator, WeatherCameraCoordinator):
            add_camera_images(hass, entry, coordinator, subentry_id, async_add_entities)


def add_camera_images(
    hass: HomeAssistant,
    entry: DigitrafficConfigEntry,
    coordinator: WeatherCameraCoordinator,
    subentry_id: str,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add an image entity for each view. The views are known once the camera has been fetched, which can be later."""
    added: set[str] = set()

    @callback
    def add_new() -> None:
        if coordinator.data is None:
            return
        entities = [CameraImage(hass, coordinator, view) for view in coordinator.data.views if view not in added]
        added.update(coordinator.data.views)
        if entities:
            async_add_entities(entities, config_subentry_id=subentry_id)

    add_new()
    entry.async_on_unload(coordinator.async_add_listener(add_new))


class CameraImage(CoordinatorEntity[WeatherCameraCoordinator], ImageEntity):
    """The latest picture from one view of a camera."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, coordinator: WeatherCameraCoordinator, view: str) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        ImageEntity.__init__(self, hass, verify_ssl=True)
        subentry = coordinator.subentry
        self._view = view
        self._taken: str | None = None
        self._attr_unique_id = f"{subentry.subentry_id}_{view}"
        # A view without a name, such as a camera's only view, is named after the camera.
        self._attr_name = coordinator.data.view_names.get(view) if coordinator.data else None
        self._attr_image_url = IMAGE_URL.format(preset=view)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, subentry.subentry_id)},
            name=subentry.title,
            manufacturer="Fintraffic",
            model_id=coordinator.camera_id,
            entry_type=DeviceEntryType.SERVICE,
        )
        self._refresh_picture_time()

    @property
    def available(self) -> bool:
        return super().available and self._view in self._picture_times()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._refresh_picture_time()
        super()._handle_coordinator_update()

    def _picture_times(self) -> dict[str, str]:
        return self.coordinator.data.picture_times if self.coordinator.data else {}

    def _refresh_picture_time(self) -> None:
        """A new picture replaces the cached one; its time is the entity's state."""
        taken = self._picture_times().get(self._view)
        if taken == self._taken:
            return
        self._taken = taken
        self._cached_image = None
        self._attr_image_last_updated = dt_util.parse_datetime(taken) if taken else None
