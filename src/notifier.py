"""Notifiers: ConsoleNotifier, WebhookNotifier, SlackNotifier, SlackBotNotifier. Interface: notify(event)."""

import logging
from typing import Optional

import requests

from .models import Event, EventType

logger = logging.getLogger(__name__)


def _format_slack_message(event: Event, ping_user_id: Optional[str] = None) -> str:
    """Build Slack message text for an event (shared by SlackNotifier and SlackBotNotifier)."""
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

    text = "\n".join(lines)
    if ping_user_id:
        text = f"<@{ping_user_id}> " + text
    return text


def _format_status_check(snapshot, url: Optional[str] = None, ping_user_id: Optional[str] = None) -> str:
    """Format a status-check message for Slack (used with --slack-test)."""
    parts = [f"  {k}: {v}" for k, v in snapshot.sections.items()]
    lines = ["*Status check*", *parts, f"  Time: {snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"]
    if url:
        lines.append(f"  URL: <{url}|View SOC>")
    text = "\n".join(lines)
    if ping_user_id:
        text = f"<@{ping_user_id}> " + text
    return text


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
        return {"text": _format_slack_message(event)}

    def notify_status(self, snapshot, url: Optional[str] = None) -> None:
        """Send status check to Slack (for --slack-test)."""
        try:
            payload = {"text": _format_status_check(snapshot, url)}
            requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
        except Exception as e:
            logger.error("Slack notify failed: %s", e)


class SlackBotNotifier:
    """Post events to Slack via Bot API (channel or DM)."""

    def __init__(self, bot_token: str, dm_user_id: str, channel: Optional[str] = None):
        self.bot_token = bot_token
        self.dm_user_id = dm_user_id
        self.channel = channel
        self._dm_channel_id: Optional[str] = None

    def _get_channel(self) -> Optional[str]:
        """Return channel ID or name for posting."""
        if self.channel:
            return self.channel
        return self._get_dm_channel()

    def notify(self, event: Event) -> None:
        """Send message to channel or DM."""
        try:
            channel_id = self._get_channel()
            if not channel_id:
                return
            text = _format_slack_message(event, ping_user_id=self.dm_user_id)
            resp = requests.post(
                "https://slack.com/api/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {self.bot_token}",
                    "Content-Type": "application/json",
                },
                json={"channel": channel_id, "text": text},
                timeout=10,
            )
            data = resp.json()
            if not data.get("ok"):
                logger.error("Slack chat.postMessage failed: %s", data.get("error", "unknown"))
        except Exception as e:
            logger.error("Slack Bot notify failed: %s", e)

    def notify_status(self, snapshot, url: Optional[str] = None) -> None:
        """Send status check to Slack."""
        try:
            channel_id = self._get_channel()
            if not channel_id:
                return
            text = _format_status_check(snapshot, url, ping_user_id=self.dm_user_id)
            resp = requests.post(
                "https://slack.com/api/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {self.bot_token}",
                    "Content-Type": "application/json",
                },
                json={"channel": channel_id, "text": text},
                timeout=10,
            )
            data = resp.json()
            if not data.get("ok"):
                logger.error("Slack chat.postMessage failed: %s", data.get("error", "unknown"))
        except Exception as e:
            logger.error("Slack Bot notify failed: %s", e)

    def _get_dm_channel(self) -> Optional[str]:
        """Open or return cached DM channel ID."""
        if self._dm_channel_id:
            return self._dm_channel_id

        try:
            resp = requests.post(
                "https://slack.com/api/conversations.open",
                headers={
                    "Authorization": f"Bearer {self.bot_token}",
                    "Content-Type": "application/json",
                },
                json={"users": [self.dm_user_id]},
                timeout=10,
            )
            data = resp.json()
            if not data.get("ok"):
                logger.error("Slack conversations.open failed: %s", data.get("error", "unknown"))
                return None

            self._dm_channel_id = data["channel"]["id"]
            return self._dm_channel_id
        except Exception as e:
            logger.error("Slack conversations.open failed: %s", e)
            return None
