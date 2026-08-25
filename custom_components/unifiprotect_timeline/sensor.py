"""Timeline sensor platform."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TimelineConfigEntry
from .coordinator import ProtectTimelineCoordinator


async def async_setup_entry(
    hass, entry: TimelineConfigEntry, async_add_entities
) -> None:
    """Create one timeline sensor for every Protect camera."""
    entities: list[ProtectTimelineSensor] = []
    for source in entry.runtime_data.sources:
        for camera_id, camera in source.cameras.items():
            entities.append(
                ProtectTimelineSensor(
                    source.coordinator,
                    source.nvr_id,
                    str(camera_id),
                    str(getattr(camera, "name", camera_id)),
                )
            )
    async_add_entities(entities)


class ProtectTimelineSensor(
    CoordinatorEntity[ProtectTimelineCoordinator], SensorEntity
):
    """Expose recent UniFi Protect events for one camera."""

    _attr_icon = "mdi:timeline-clock-outline"

    def __init__(
        self,
        coordinator: ProtectTimelineCoordinator,
        nvr_id: str,
        camera_id: str,
        camera_name: str,
    ) -> None:
        super().__init__(coordinator)
        self._camera_id = camera_id
        self._attr_unique_id = f"{nvr_id}_{camera_id}_timeline"
        self._attr_name = f"{camera_name} Timeline"

    @property
    def native_value(self) -> int:
        """Return the number of events in the configured history window."""
        return len(self.coordinator.data.get(self._camera_id, []))

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Return normalized timeline events for dashboard cards."""
        return {"events": self.coordinator.data.get(self._camera_id, [])}
