"""CLI entrypoint: soc-watch."""

import argparse

from dotenv import load_dotenv

load_dotenv()

import logging
import sys

from .config import AvailabilityRule, load_config
from .runner import run_loop


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="soc-watch",
        description="UCLA SOC Availability Watcher - monitor course pages for seat openings",
    )
    parser.add_argument("--url", help="SOC results URL to monitor")
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Poll interval in seconds (default: 60)",
    )
    parser.add_argument(
        "--rule",
        choices=[
            AvailabilityRule.ANY_OPEN,
            AvailabilityRule.LECTURE_AND_DISCUSSION,
            AvailabilityRule.SPECIFIC_SECTIONS,
        ],
        default=AvailabilityRule.ANY_OPEN,
        help="Availability rule (default: any_open)",
    )
    parser.add_argument(
        "--sections",
        help="Comma-separated section IDs for specific_sections rule (e.g. Lec 1,Dis 1A)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (for debugging)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose logging",
    )
    parser.add_argument(
        "--slack-webhook",
        help="Slack Incoming Webhook URL for notifications on availability changes",
    )
    parser.add_argument(
        "--slack-bot-token",
        help="Slack Bot User OAuth Token (xoxb-...) for DM notifications",
    )
    parser.add_argument(
        "--slack-dm-user",
        help="Slack User ID (U0xxxxx) to receive DM notifications",
    )
    parser.add_argument(
        "--slack-channel",
        help="Slack channel (e.g. #general) to post to instead of DM; pings --slack-dm-user",
    )
    parser.add_argument(
        "--slack-test",
        action="store_true",
        help="Send Slack message on every check (for testing)",
    )

    args = parser.parse_args()
    sections = [s.strip() for s in args.sections.split(",")] if args.sections else None

    if args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    config = load_config(
        url=args.url,
        interval=args.interval,
        sections=sections,
        rule=args.rule,
        verbose=args.verbose,
        slack_webhook=args.slack_webhook,
        slack_bot_token=args.slack_bot_token,
        slack_dm_user_id=args.slack_dm_user,
        slack_channel=args.slack_channel,
        slack_test=args.slack_test,
    )

    try:
        run_loop(config, once=args.once)
    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
