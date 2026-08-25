"""Pure event normalization helpers."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any


def normalize_event_type(event: dict[str, Any]) -> str:
    """Return a stable, human-readable event type."""
    event_type = str(event.get("type") or "motion")
    if event_type != "smartDetectZone":
        return event_type

    smart_types = event.get("smartDetectTypes")
    if isinstance(smart_types, list) and smart_types:
        return str(smart_types[0])
    return event_type


def normalize_events(
    events: Iterable[dict[str, Any]],
    *,
    camera_id: str,
    nvr_id: str,
    max_events: int,
    video_url_factory: Any,
    thumbnail_url_factory: Any,
) -> list[dict[str, str]]:
    """Filter, sort, deduplicate, and serialize events for one camera."""
    rows: list[tuple[str, datetime, str]] = []

    for event in events:
        event_id = event.get("id") or event.get("event_id")
        event_camera_id = event.get("camera") or event.get("camera_id")
        start_ms = event.get("start")
        if not event_id or event_camera_id != camera_id or not start_ms:
            continue

        try:
            started = datetime.fromtimestamp(float(start_ms) / 1000, tz=UTC)
        except (TypeError, ValueError, OSError):
            continue

        rows.append((str(event_id), started, normalize_event_type(event)))

    rows.sort(key=lambda row: row[1], reverse=True)
    seen: set[str] = set()
    result: list[dict[str, str]] = []
    for event_id, started, event_type in rows:
        if event_id in seen:
            continue
        seen.add(event_id)
        result.append(
            {
                "id": event_id,
                "timestamp": started.isoformat(),
                "url": video_url_factory(nvr_id, event_id),
                "snapshot": thumbnail_url_factory(event_id, nvr_id),
                "type": event_type,
            }
        )
        if len(result) >= max_events:
            break

    return result

