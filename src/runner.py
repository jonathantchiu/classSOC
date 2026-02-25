"""Orchestration loop: fetch → parse → detect → notify → persist → sleep."""

import logging
import time
from typing import Optional

from .config import Config
from .detector import detect
from .fetcher import fetch_html
from .models import Snapshot
from .notifier import ConsoleNotifier, SlackBotNotifier, SlackNotifier
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
    slack_notifiers = []
    if config.slack_webhook_url:
        n = SlackNotifier(config.slack_webhook_url)
        notifiers.append(n)
        slack_notifiers.append(n)
    if config.slack_bot_token and config.slack_dm_user_id:
        n = SlackBotNotifier(
            config.slack_bot_token,
            config.slack_dm_user_id,
            channel=config.slack_channel,
        )
        notifiers.append(n)
        slack_notifiers.append(n)

    for event in events:
        for notifier in notifiers:
            notifier.notify(event)

    # Always send status to Slack on every poll (even when closed)
    if slack_notifiers:
        for n in slack_notifiers:
            n.notify_status(snapshot, target_url)

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
