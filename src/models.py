"""Data models for UCLA SOC Availability Watcher."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Status(str, Enum):
    """Normalized section availability status."""

    OPEN = "OPEN"
    CLOSED = "CLOSED"
    WAITLISTED = "WAITLISTED"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"


@dataclass
class Snapshot:
    """Snapshot of section statuses at a point in time."""

    timestamp: datetime
    sections: dict[str, str]  # label -> normalized_status
    raw: Optional[dict[str, str]] = None  # label -> raw_text
    meta: Optional[dict[str, str]] = None  # term, course, classid

    def to_dict(self) -> dict:
        """Serialize for JSON persistence."""
        d = {
            "timestamp": self.timestamp.isoformat(),
            "sections": self.sections,
        }
        if self.raw is not None:
            d["raw"] = self.raw
        if self.meta is not None:
            d["meta"] = self.meta
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Snapshot":
        """Deserialize from JSON."""
        return cls(
            timestamp=datetime.fromisoformat(d["timestamp"]),
            sections=d["sections"],
            raw=d.get("raw"),
            meta=d.get("meta"),
        )


class EventType(str, Enum):
    """Event types emitted by the detector."""

    BECAME_AVAILABLE = "BECAME_AVAILABLE"
    BECAME_UNAVAILABLE = "BECAME_UNAVAILABLE"
    STATUS_CHANGED = "STATUS_CHANGED"


@dataclass
class Event:
    """Event emitted when availability changes."""

    type: EventType
    timestamp: datetime
    curr_snapshot: Snapshot
    prev_snapshot: Optional[Snapshot] = None
    diff: list[str] = field(default_factory=list)
    url: Optional[str] = None
