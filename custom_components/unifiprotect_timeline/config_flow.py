"""Config and options flows for UniFi Protect Timeline."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    CONF_HISTORY_HOURS,
    CONF_MAX_EVENTS,
    CONF_SCAN_INTERVAL,
    DEFAULT_HISTORY_HOURS,
    DEFAULT_MAX_EVENTS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)


class UnifiProtectTimelineConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the UniFi Protect Timeline config flow."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Create the singleton integration entry."""
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="UniFi Protect Timeline", data={})
        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow."""
        return TimelineOptionsFlow()


class TimelineOptionsFlow(config_entries.OptionsFlow):
    """Configure history and polling settings."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage integration options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        options = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HISTORY_HOURS,
                        default=options.get(CONF_HISTORY_HOURS, DEFAULT_HISTORY_HOURS),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=168)),
                    vol.Required(
                        CONF_MAX_EVENTS,
                        default=options.get(CONF_MAX_EVENTS, DEFAULT_MAX_EVENTS),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    ): vol.All(vol.Coerce(int), vol.Range(min=30, max=3600)),
                }
            ),
        )

