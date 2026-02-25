"""Detector: compare snapshots, apply availability rule, emit events."""

from datetime import datetime, timezone
from typing import Callable, Optional

from .config import AvailabilityRule, Config
from .models import Event, EventType, Snapshot, Status


def _is_available_any_open(sections: dict[str, str], _config: Config) -> bool:
    """Rule A: available if any section is OPEN."""
    return Status.OPEN.value in sections.values()


def _is_available_lecture_and_discussion(sections: dict[str, str], _config: Config) -> bool:
    """Rule B: lecture OPEN and at least one discussion OPEN."""
    has_lec_open = any(
        k.lower().startswith("lec") and v == Status.OPEN.value
        for k, v in sections.items()
    )
    has_disc_open = any(
        k.lower().startswith("dis") and v == Status.OPEN.value
        for k, v in sections.items()
    )
    return bool(has_lec_open and has_disc_open)


def _is_available_specific_sections(sections: dict[str, str], config: Config) -> bool:
    """Rule C: only watched sections must be OPEN."""
    if not config.watched_sections:
        return _is_available_any_open(sections, config)
    return all(
        sections.get(s, "") == Status.OPEN.value
        for s in config.watched_sections
    )


RULE_FUNCS: dict[str, Callable[[dict[str, str], Config], bool]] = {
    AvailabilityRule.ANY_OPEN: _is_available_any_open,
    AvailabilityRule.LECTURE_AND_DISCUSSION: _is_available_lecture_and_discussion,
    AvailabilityRule.SPECIFIC_SECTIONS: _is_available_specific_sections,
}


def _get_rule_func(rule: str) -> Callable[[dict[str, str], Config], bool]:
    """Resolve rule name to function."""
    return RULE_FUNCS.get(rule, _is_available_any_open)


def _diff_labels(prev: Snapshot, curr: Snapshot) -> list[str]:
    """Labels that changed between snapshots."""
    changed = []
    all_labels = set(prev.sections.keys()) | set(curr.sections.keys())
    for label in all_labels:
        p = prev.sections.get(label)
        c = curr.sections.get(label)
        if p != c:
            changed.append(label)
    return changed


def detect(
    prev: Optional[Snapshot],
    curr: Snapshot,
    config: Config,
    url: Optional[str] = None,
) -> list[Event]:
    """
    Compare prev vs curr, apply availability rule, emit events.
    """
    events: list[Event] = []
    rule_func = _get_rule_func(config.rule)
    curr_avail = rule_func(curr.sections, config)

    if prev is None:
        # First run: no events, just establish baseline
        return events

    prev_avail = rule_func(prev.sections, config)
    diff = _diff_labels(prev, curr)

    if curr_avail and not prev_avail:
        events.append(Event(
            type=EventType.BECAME_AVAILABLE,
            timestamp=datetime.now(timezone.utc),
            prev_snapshot=prev,
            curr_snapshot=curr,
            diff=diff,
            url=url,
        ))
    elif not curr_avail and prev_avail:
        events.append(Event(
            type=EventType.BECAME_UNAVAILABLE,
            timestamp=datetime.now(timezone.utc),
            prev_snapshot=prev,
            curr_snapshot=curr,
            diff=diff,
            url=url,
        ))
    elif diff:
        events.append(Event(
            type=EventType.STATUS_CHANGED,
            timestamp=datetime.now(timezone.utc),
            prev_snapshot=prev,
            curr_snapshot=curr,
            diff=diff,
            url=url,
        ))

    return events
