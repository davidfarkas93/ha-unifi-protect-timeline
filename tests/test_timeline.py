"""Tests for event normalization."""

import importlib.util
from datetime import UTC, datetime
from pathlib import Path

MODULE_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "unifiprotect_timeline"
    / "timeline.py"
)
SPEC = importlib.util.spec_from_file_location("timeline", MODULE_PATH)
assert SPEC and SPEC.loader
timeline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(timeline)


def _video(nvr_id: str, event_id: str) -> str:
    return f"/video/{nvr_id}/{event_id}"


def _thumbnail(event_id: str, nvr_id: str) -> str:
    return f"/thumbnail/{nvr_id}/{event_id}"


def test_normalize_events_filters_sorts_and_deduplicates() -> None:
    """Only valid events for the requested camera are returned newest-first."""
    events = [
        {"id": "old", "camera": "cam-1", "start": 1_700_000_000_000, "end": 1},
        {
            "id": "new",
            "camera": "cam-1",
            "start": 1_710_000_000_000,
            "end": 1,
            "type": "smartDetectZone",
            "smartDetectTypes": ["person"],
        },
        {"id": "new", "camera": "cam-1", "start": 1_710_000_000_000, "end": 1},
        {"id": "other", "camera": "cam-2", "start": 1_720_000_000_000, "end": 1},
        {
            "id": "admin",
            "camera": "cam-1",
            "start": 1_730_000_000_000,
            "type": "adminActivity",
        },
        {"id": "invalid", "camera": "cam-1", "start": "bad", "end": 1},
    ]

    result = timeline.normalize_events(
        events,
        camera_id="cam-1",
        nvr_id="nvr-1",
        max_events=10,
        video_url_factory=_video,
        thumbnail_url_factory=_thumbnail,
    )

    assert [event["id"] for event in result] == ["new", "old"]
    assert result[0]["type"] == "person"
    assert result[0]["url"] == "/video/nvr-1/new"
    assert result[0]["snapshot"] == "/thumbnail/nvr-1/new"
    assert result[0]["timestamp"] == datetime.fromtimestamp(
        1_710_000_000, tz=UTC
    ).isoformat()


def test_normalize_events_honors_limit() -> None:
    """The per-camera result never exceeds the configured maximum."""
    events = [
        {"id": str(index), "camera_id": "cam", "start": index * 1000, "end": 1}
        for index in range(5)
    ]
    result = timeline.normalize_events(
        events,
        camera_id="cam",
        nvr_id="nvr",
        max_events=2,
        video_url_factory=_video,
        thumbnail_url_factory=_thumbnail,
    )
    assert [event["id"] for event in result] == ["4", "3"]


def test_smart_detection_without_types_falls_back() -> None:
    """Malformed smart detection data remains representable."""
    assert (
        timeline.normalize_event_type({"type": "smartDetectZone"})
        == "smartDetectZone"
    )
