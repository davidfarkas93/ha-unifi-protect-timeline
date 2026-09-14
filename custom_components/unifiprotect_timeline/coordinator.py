"""Shared event coordinator for UniFi Protect Timeline."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from homeassistant.components.unifiprotect.views import (
    async_generate_proxy_event_video_url,
    async_generate_thumbnail_url,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from uiprotect.data import EventType

from .const import DOMAIN
from .timeline import merge_normalized_events, normalize_events

_LOGGER = logging.getLogger(__name__)
CoordinatorData = dict[str, list[dict[str, str]]]

# Ask Protect only for camera events that can have playable media. Passing
# ``types=None`` makes uiprotect work around a Protect API bug by iterating over
# every matching event, including audit, connection, and configuration records.
MEDIA_EVENT_TYPES = [
    EventType.MOTION,
    EventType.RING,
    EventType.SMART_DETECT,
    EventType.SMART_DETECT_LINE,
    EventType.SMART_DETECT_LOITER,
    EventType.SMART_AUDIO_DETECT,
]
QUERY_OVERLAP = timedelta(seconds=10)


class ProtectTimelineCoordinator(DataUpdateCoordinator[CoordinatorData]):
    """Fetch an NVR timeline once and distribute it to camera entities."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: Any,
        nvr_id: str,
        camera_ids: set[str],
        *,
        history_hours: int,
        max_events: int,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{nvr_id}",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.api = api
        self.nvr_id = nvr_id
        self.camera_ids = camera_ids
        self.history_hours = history_hours
        self.max_events = max_events
        self._last_query_end: datetime | None = None

    async def _async_update_data(self) -> CoordinatorData:
        now = datetime.now(UTC)
        history_start = now - timedelta(hours=self.history_hours)
        query_start = history_start
        if self._last_query_end is not None:
            query_start = max(history_start, self._last_query_end - QUERY_OVERLAP)

        try:
            raw_events = await self.api.get_events_raw(
                start=query_start,
                end=now,
                types=MEDIA_EVENT_TYPES,
                limit=max(100, self.max_events * len(self.camera_ids)),
                sorting="desc",
            )
        except Exception as err:
            raise UpdateFailed(f"Unable to fetch UniFi Protect events: {err}") from err

        previous_data = self.data or {}
        updated_data = {
            camera_id: merge_normalized_events(
                previous_data.get(camera_id, []),
                normalize_events(
                    raw_events,
                    camera_id=camera_id,
                    nvr_id=self.nvr_id,
                    max_events=self.max_events,
                    video_url_factory=async_generate_proxy_event_video_url,
                    thumbnail_url_factory=lambda event_id, nvr_id: (
                        async_generate_thumbnail_url(
                            event_id, nvr_id, width=480, height=270
                        )
                    ),
                ),
                cutoff=history_start,
                max_events=self.max_events,
            )
            for camera_id in self.camera_ids
        }
        self._last_query_end = now
        return updated_data
