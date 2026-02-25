"""Test detector: full→open emits BECAME_AVAILABLE."""

from datetime import datetime, timezone
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import EventType, Snapshot
from src.config import Config, AvailabilityRule
from src.detector import detect


def test_full_to_open_emits_became_available():
    prev = Snapshot(
        timestamp=datetime.now(timezone.utc),
        sections={"Lec 1": "CLOSED", "Dis 1A": "CLOSED"},
    )
    curr = Snapshot(
        timestamp=datetime.now(timezone.utc),
        sections={"Lec 1": "OPEN", "Dis 1A": "OPEN"},
    )
    config = Config(url="https://example.com", rule=AvailabilityRule.ANY_OPEN)
    events = detect(prev, curr, config)
    assert len(events) == 1
    assert events[0].type == EventType.BECAME_AVAILABLE
    assert "Lec 1" in events[0].diff or "Dis 1A" in events[0].diff
