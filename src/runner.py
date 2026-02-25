"""Orchestration loop: fetch → parse → detect → notify → persist → sleep."""

import logging
import time
from typing import Optional

from .config import Config
from .detector import detect
from .fetcher import fetch_html
from .models import Snapshot
from .notifier import ConsoleNotifier, SlackNotifier
from .parser import parse
from .state import load_last_snapshot, save_snapshot

logger = logging.getLogger(__name__)


def run_once(config: Config, url: Optional[str] = None) -> bool:
    """
    Run one poll cycle. Returns True if successful.
    On parse failure: log, do not overwrite last good snapshot.
    """
    target_url = url or config.url
    if not target_url:
        logger.error("No URL configured")
        return False

    html = fetch_html(target_url)
    if html is None:
        logger.error("Fetch failed")
        return False

    snapshot = parse(html)
    if snapshot is None:
        logger.error("Parse failed; not overwriting last good state")
        return False

    prev = load_last_snapshot()
    events = detect(prev, snapshot, config, url=target_url)

    notifiers = [ConsoleNotifier()]
    if config.slack_webhook_url:
        notifiers.append(SlackNotifier(config.slack_webhook_url))
    for event in events:
        for notifier in notifiers:
            notifier.notify(event)

    # Log status line
    if config.verbose:
        parts = [f"{k}: {v}" for k, v in snapshot.sections.items()]
        logger.info("[%s] %s", snapshot.timestamp.strftime("%Y-%m-%d %H:%M:%S"), " | ".join(parts))
    else:
        parts = [f"{k}: {v}" for k, v in snapshot.sections.items()]
        print(f"[{snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {' | '.join(parts)}")

    save_snapshot(snapshot)
    return True


def run_loop(config: Config, once: bool = False) -> None:
    """Main loop: poll at interval until interrupted or --once."""
    url = config.url
    if not url:
        print("Error: --url or SOC_URL required")
        return

    if once:
        run_once(config, url)
        return

    while True:
        run_once(config, url)
        time.sleep(config.interval_sec)
