"""State persistence: load/save snapshot to .state/last.json."""

import json
import logging
from pathlib import Path
from typing import Optional

from .models import Snapshot

logger = logging.getLogger(__name__)

STATE_DIR = Path(".state")
STATE_FILE = STATE_DIR / "last.json"


def load_last_snapshot() -> Optional[Snapshot]:
    """Load last snapshot from disk. Returns None if not found or invalid."""
    if not STATE_FILE.exists():
        return None
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            d = json.load(f)
        return Snapshot.from_dict(d)
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.warning("Failed to load state: %s", e)
        return None


def save_snapshot(snapshot: Snapshot) -> None:
    """Persist snapshot to disk."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(snapshot.to_dict(), f, indent=2)
