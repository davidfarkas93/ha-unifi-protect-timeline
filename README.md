# UniFi Protect Timeline for Home Assistant

A backend-only Home Assistant custom integration providing a normalized timeline
of UniFi Protect camera events, authenticated snapshots, and recordings.

The integration intentionally contains no frontend code. It exposes one sensor
per camera; dashboards and custom cards can render the `events` attribute in any
visual style. It works particularly well as the data source for Luma's timeline
card, but does not depend on Luma.

## Features

- Discovers cameras from every loaded core UniFi Protect integration.
- Fetches each NVR timeline once per refresh instead of once per camera.
- Loads the configured history window only at startup, then requests new events
  incrementally with a small overlap for reliable deduplication.
- Exposes authenticated Home Assistant proxy URLs for thumbnails and videos.
- Normalizes motion and smart-detection event types.
- Requests only playable camera event types and defensively filters connection,
  configuration, and audit records that have no thumbnail or recording.
- Deduplicates and sorts events newest-first.
- Marks entities unavailable when Protect requests fail.
- Configurable history window, per-camera event limit, and refresh interval.
- English and Hungarian setup translations.

## Requirements

- Home Assistant 2026.8 or newer.
- The built-in **UniFi Protect** integration configured and loaded.
- Recording access for the UniFi Protect user configured in Home Assistant.

## Installation with HACS

1. Open HACS and add `davidfarkas93/ha-unifi-protect-timeline` as a custom
   **Integration** repository.
2. Install **UniFi Protect Timeline**.
3. Restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration** and select
   **UniFi Protect Timeline**.

The integration is a singleton. One entry discovers cameras from all loaded
UniFi Protect config entries.

## Configuration

Open the integration's **Configure** dialog to change:

| Option | Default | Range |
|---|---:|---:|
| History window | 48 hours | 1–168 hours |
| Maximum events | 30 per camera | 1–100 |
| Refresh interval | 300 seconds | 30–3600 seconds |

Larger windows and limits increase Protect API work and Home Assistant state
attribute size. Keep the defaults unless the dashboard needs more history.

## Sensor data

Each camera gets a sensor whose state is the number of currently exposed events.
Its `events` attribute is a newest-first list:

```json
[
  {
    "id": "event-id",
    "timestamp": "2026-08-21T12:34:56+00:00",
    "url": "/api/unifiprotect/event/.../video",
    "snapshot": "/api/unifiprotect/thumbnail/...",
    "type": "person"
  }
]
```

The URLs require an authenticated Home Assistant session. The integration never
copies UniFi Protect credentials into entity state.

## Removal

Remove the config entry from **Settings → Devices & services**, then uninstall
the repository in HACS and restart Home Assistant.

## Development

```bash
python -m pip install -e '.[test]'
ruff check .
pytest
```

## License

MIT
