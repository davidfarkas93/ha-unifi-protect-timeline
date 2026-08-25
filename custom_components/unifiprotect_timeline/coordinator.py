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

from .const import DOMAIN
from .timeline import normalize_events

_LOGGER = logging.getLogger(__name__)
CoordinatorData = dict[str, list[dict[str, str]]]


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

    async def _async_update_data(self) -> CoordinatorData:
        now = datetime.now(UTC)
        try:
            raw_events = await self.api.get_events_raw(
                start=now - timedelta(hours=self.history_hours),
                end=now,
                types=None,
                limit=max(100, self.max_events * len(self.camera_ids)),
                sorting="sorting",
            )
        except Exception as err:
            raise UpdateFailed(f"Unable to fetch UniFi Protect events: {err}") from err

        return {
            camera_id: normalize_events(
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
            )
            for camera_id in self.camera_ids
        }
