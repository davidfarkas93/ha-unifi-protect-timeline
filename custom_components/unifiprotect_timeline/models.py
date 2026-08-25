"""Runtime models for UniFi Protect Timeline."""

from dataclasses import dataclass
from typing import Any

from .coordinator import ProtectTimelineCoordinator


@dataclass(slots=True)
class TimelineSource:
    """One loaded UniFi Protect NVR and its shared coordinator."""

    api: Any
    nvr_id: str
    cameras: dict[str, Any]
    coordinator: ProtectTimelineCoordinator


@dataclass(slots=True)
class TimelineRuntimeData:
    """Runtime data stored on the config entry."""

    sources: list[TimelineSource]

