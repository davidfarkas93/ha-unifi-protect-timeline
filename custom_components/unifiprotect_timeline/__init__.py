"""UniFi Protect Timeline integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    CONF_HISTORY_HOURS,
    CONF_MAX_EVENTS,
    CONF_SCAN_INTERVAL,
    DEFAULT_HISTORY_HOURS,
    DEFAULT_MAX_EVENTS,
    DEFAULT_SCAN_INTERVAL,
    PLATFORMS,
)
from .coordinator import ProtectTimelineCoordinator
from .models import TimelineRuntimeData, TimelineSource

type TimelineConfigEntry = ConfigEntry[TimelineRuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: TimelineConfigEntry) -> bool:
    """Set up UniFi Protect Timeline from a config entry."""
    sources: list[TimelineSource] = []
    options = entry.options

    for protect_entry in hass.config_entries.async_entries("unifiprotect"):
        if protect_entry.state is not ConfigEntryState.LOADED:
            continue
        runtime = getattr(protect_entry, "runtime_data", None)
        api = getattr(runtime, "api", None)
        bootstrap = getattr(api, "bootstrap", None)
        if api is None or bootstrap is None:
            continue

        cameras = dict(bootstrap.cameras)
        coordinator = ProtectTimelineCoordinator(
            hass,
            entry,
            api,
            str(bootstrap.nvr.id),
            set(cameras),
            history_hours=options.get(CONF_HISTORY_HOURS, DEFAULT_HISTORY_HOURS),
            max_events=options.get(CONF_MAX_EVENTS, DEFAULT_MAX_EVENTS),
            scan_interval=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        await coordinator.async_config_entry_first_refresh()
        sources.append(TimelineSource(api, str(bootstrap.nvr.id), cameras, coordinator))

    if not sources:
        raise ConfigEntryNotReady("No loaded UniFi Protect integration was found")

    entry.runtime_data = TimelineRuntimeData(sources)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: TimelineConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(
    hass: HomeAssistant, entry: TimelineConfigEntry
) -> None:
    """Reload after options change."""
    await hass.config_entries.async_reload(entry.entry_id)
