"""Constants for UniFi Protect Timeline."""

from homeassistant.const import Platform

DOMAIN = "unifiprotect_timeline"
PLATFORMS = (Platform.SENSOR,)

CONF_HISTORY_HOURS = "history_hours"
CONF_MAX_EVENTS = "max_events"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_HISTORY_HOURS = 48
DEFAULT_MAX_EVENTS = 30
DEFAULT_SCAN_INTERVAL = 300

