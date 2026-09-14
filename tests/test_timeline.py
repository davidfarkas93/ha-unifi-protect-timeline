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
        {
            "id": "connected",
            "camera": "cam-1",
            "start": 1_740_000_000_000,
            "type": "cameraConnected",
        },
        {
            "id": "disconnected",
            "camera": "cam-1",
            "start": 1_750_000_000_000,
            "type": "disconnect",
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


def test_all_supported_media_event_types_are_kept() -> None:
    """Every requested Protect media event type remains representable."""
    events = [
        {
            "id": event_type,
            "camera": "cam",
            "start": (index + 1) * 1000,
            "type": event_type,
        }
        for index, event_type in enumerate(sorted(timeline.MEDIA_EVENT_TYPES))
    ]

    result = timeline.normalize_events(
        events,
        camera_id="cam",
        nvr_id="nvr",
        max_events=20,
        video_url_factory=_video,
        thumbnail_url_factory=_thumbnail,
    )

    assert {event["type"] for event in result} == timeline.MEDIA_EVENT_TYPES


def test_incremental_results_are_merged_pruned_and_deduplicated() -> None:
    """Incoming updates replace cached rows without losing recent history."""
    existing = [
        {"id": "old", "timestamp": "2024-01-01T00:00:00+00:00", "type": "motion"},
        {"id": "same", "timestamp": "2024-01-03T00:00:00+00:00", "type": "motion"},
        {"id": "kept", "timestamp": "2024-01-02T00:00:00+00:00", "type": "motion"},
    ]
    incoming = [
        {"id": "new", "timestamp": "2024-01-04T00:00:00+00:00", "type": "person"},
        {"id": "same", "timestamp": "2024-01-03T00:00:00+00:00", "type": "person"},
    ]

    result = timeline.merge_normalized_events(
        existing,
        incoming,
        cutoff=datetime(2024, 1, 2, tzinfo=UTC),
        max_events=3,
    )

    assert [event["id"] for event in result] == ["new", "same", "kept"]
    assert result[1]["type"] == "person"
