# UCLA SOC Availability Watcher

A lightweight polling system that monitors UCLA Schedule of Classes (SOC) course pages and notifies you when a class transitions from full/closed to available/open.

## Install

```bash
pip install -e .
```

## Usage

```bash
# Monitor a SOC URL (required)
soc-watch --url "https://sa.ucla.edu/ro/ClassSearch/Results/..."

# Poll every 60 seconds (default)
soc-watch --url "..." --interval 60

# Use lecture + discussion rule (class available when Lec AND at least one Dis are OPEN)
soc-watch --url "..." --rule lecture_and_discussion

# Run once and exit (for debugging)
soc-watch --url "..." --once

# Verbose logging
soc-watch --url "..." --verbose

# Slack notifications on availability changes
soc-watch --url "..." --slack-webhook "https://hooks.slack.com/services/..."
```

## Environment Variables

- `SOC_URL` — SOC results URL
- `SOC_INTERVAL_SEC` — Poll interval (default: 60)
- `SOC_RULE` — `any_open`, `lecture_and_discussion`, or `specific_sections`
- `SOC_SECTIONS` — Comma-separated section IDs for `specific_sections` rule (e.g. `Lec 1,Dis 1A`)
- `SOC_SLACK_WEBHOOK` — Slack Incoming Webhook URL for notifications on availability changes

## Availability Rules

| Rule | Description |
|------|-------------|
| `any_open` | Available if any section is OPEN |
| `lecture_and_discussion` | Available if lecture AND at least one discussion are OPEN |
| `specific_sections` | Only watched sections (from `--sections` or `SOC_SECTIONS`) must be OPEN |

## State

Last snapshot is persisted to `.state/last.json` so restarts still catch transitions.

## Tests

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Project Structure

```
src/
  config.py    # URL, interval, sections, rule
  fetcher.py   # fetch_html(url)
  parser.py    # parse(html) -> Snapshot
  state.py     # load/save snapshot
  detector.py  # detect(prev, curr) -> list[Event]
  notifier.py  # ConsoleNotifier; notify(event)
  runner.py    # Orchestration loop
  cli.py       # soc-watch entrypoint
tests/
  fixtures/    # full_closed.html, open.html, waitlisted.html
  test_parser.py
  test_detector.py
```
