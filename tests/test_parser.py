"""Test parser returns expected normalized statuses per fixture."""

from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parser import parse
from src.models import Status

FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> str:
    with open(FIXTURES / name, encoding="utf-8") as f:
        return f.read()


def test_parse_full_closed():
    html = _load_fixture("full_closed.html")
    snapshot = parse(html)
    assert snapshot is not None
    assert snapshot.sections["Lec 1"] == Status.CLOSED.value
    assert snapshot.sections["Dis 1A"] == Status.CLOSED.value


def test_parse_open():
    html = _load_fixture("open.html")
    snapshot = parse(html)
    assert snapshot is not None
    assert snapshot.sections["Lec 1"] == Status.OPEN.value
    assert snapshot.sections["Dis 1A"] == Status.OPEN.value


def test_parse_waitlisted():
    html = _load_fixture("waitlisted.html")
    snapshot = parse(html)
    assert snapshot is not None
    assert snapshot.sections["Lec 1"] == Status.WAITLISTED.value
    assert snapshot.sections["Dis 1A"] == Status.WAITLISTED.value
