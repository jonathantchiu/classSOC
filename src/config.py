"""Configuration: env vars, defaults, URL, interval, sections, rule."""

import os
from dataclasses import dataclass
from typing import Optional


class AvailabilityRule:
    """Availability rule names."""

    ANY_OPEN = "any_open"
    LECTURE_AND_DISCUSSION = "lecture_and_discussion"
    SPECIFIC_SECTIONS = "specific_sections"


@dataclass
class Config:
    """Application configuration."""

    url: str
    interval_sec: int = 60
    watched_sections: Optional[list[str]] = None
    rule: str = AvailabilityRule.ANY_OPEN
    verbose: bool = False
    slack_webhook_url: Optional[str] = None
    slack_bot_token: Optional[str] = None
    slack_dm_user_id: Optional[str] = None
    slack_channel: Optional[str] = None
    slack_test: bool = False


def load_config(
    url: Optional[str] = None,
    interval: Optional[int] = None,
    sections: Optional[list[str]] = None,
    rule: Optional[str] = None,
    verbose: bool = False,
    slack_webhook: Optional[str] = None,
    slack_bot_token: Optional[str] = None,
    slack_dm_user_id: Optional[str] = None,
    slack_channel: Optional[str] = None,
    slack_test: bool = False,
) -> Config:
    """Load config from env vars with overrides from CLI."""
    return Config(
        url=url or os.environ.get("SOC_URL", ""),
        interval_sec=interval or int(os.environ.get("SOC_INTERVAL_SEC", "60")),
        watched_sections=sections or _parse_sections(os.environ.get("SOC_SECTIONS", "")),
        rule=rule or os.environ.get("SOC_RULE", AvailabilityRule.ANY_OPEN),
        verbose=verbose or os.environ.get("SOC_VERBOSE", "").lower() in ("1", "true", "yes"),
        slack_webhook_url=slack_webhook or os.environ.get("SOC_SLACK_WEBHOOK") or None,
        slack_bot_token=slack_bot_token or os.environ.get("SOC_SLACK_BOT_TOKEN") or None,
        slack_dm_user_id=slack_dm_user_id or os.environ.get("SOC_SLACK_DM_USER_ID") or None,
        slack_channel=slack_channel or os.environ.get("SOC_SLACK_CHANNEL") or None,
        slack_test=slack_test or os.environ.get("SOC_SLACK_TEST", "").lower() in ("1", "true", "yes"),
    )


def _parse_sections(s: str) -> Optional[list[str]]:
    """Parse comma-separated sections list."""
    if not s or not s.strip():
        return None
    return [x.strip() for x in s.split(",") if x.strip()]
