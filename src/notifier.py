"""Notifiers: ConsoleNotifier, WebhookNotifier, SlackNotifier. Interface: notify(event)."""

import logging
from typing import Optional

import requests

from .models import Event, EventType

logger = logging.getLogger(__name__)


class ConsoleNotifier:
    """Print events to console."""

    def notify(self, event: Event) -> None:
        """Emit event to console."""
        if event.type == EventType.BECAME_AVAILABLE:
            self._notify_available(event)
        elif event.type == EventType.BECAME_UNAVAILABLE:
            self._notify_unavailable(event)
        else:
            self._notify_status_changed(event)

    def _notify_available(self, event: Event) -> None:
        lines = [
            "",
            "🎉 CLASS AVAILABLE",
            *[f"  {k}: {v}" for k, v in event.curr_snapshot.sections.items()],
            f"  Time: {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        if event.url:
            lines.append(f"  URL: {event.url}")
        print("\n".join(lines))

    def _notify_unavailable(self, event: Event) -> None:
        print(f"\n⚠️ Class no longer available. Sections: {event.curr_snapshot.sections}")

    def _notify_status_changed(self, event: Event) -> None:
        print(f"\n📋 Status changed: {event.diff} -> {event.curr_snapshot.sections}")


class WebhookNotifier:
    """POST event to a webhook URL (Discord, Slack, etc.)."""

    def __init__(self, url: str):
        self.url = url

    def notify(self, event: Event) -> None:
        """POST event payload to webhook."""
        try:
            payload = self._build_payload(event)
            requests.post(self.url, json=payload, timeout=10)
        except Exception as e:
            logger.error("Webhook notify failed: %s", e)

    def _build_payload(self, event: Event) -> dict:
        """Build webhook payload."""
        return {
            "type": event.type.value,
            "timestamp": event.timestamp.isoformat(),
            "sections": event.curr_snapshot.sections,
            "diff": event.diff,
            "url": event.url,
        }


class SlackNotifier:
    """Post events to Slack via Incoming Webhook."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def notify(self, event: Event) -> None:
        """Post event to Slack."""
        try:
            payload = self._build_payload(event)
            requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
        except Exception as e:
            logger.error("Slack notify failed: %s", e)

    def _build_payload(self, event: Event) -> dict:
        """Build Slack Incoming Webhook payload with text field."""
        lines = []
        if event.type == EventType.BECAME_AVAILABLE:
            lines.append("*CLASS AVAILABLE*")
            for k, v in event.curr_snapshot.sections.items():
                lines.append(f"  {k}: {v}")
        elif event.type == EventType.BECAME_UNAVAILABLE:
            lines.append("*Class no longer available*")
            lines.append(f"  Sections: {event.curr_snapshot.sections}")
        else:
            lines.append("*Status changed*")
            lines.append(f"  Changed: {event.diff}")
            lines.append(f"  Sections: {event.curr_snapshot.sections}")

        lines.append(f"  Time: {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        if event.url:
            lines.append(f"  URL: <{event.url}|View SOC>")

        return {"text": "\n".join(lines)}
