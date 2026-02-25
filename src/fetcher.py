"""HTTP fetcher with retry/backoff for UCLA SOC pages."""

import logging
import time
from typing import Optional

import requests

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0"
)
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0


def fetch_html(url: str) -> Optional[str]:
    """
    Fetch HTML from URL with retry/backoff for 429/5xx.
    Returns None on failure.
    """
    session = requests.Session()
    session.headers["User-Agent"] = DEFAULT_USER_AGENT

    for attempt in range(MAX_RETRIES):
        try:
            resp = session.get(url, timeout=DEFAULT_TIMEOUT)
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", RETRY_BACKOFF))
                logger.warning("Rate limited (429), retrying after %s sec", retry_after)
                time.sleep(retry_after)
                continue
            if resp.status_code >= 500:
                logger.warning("Server error %s, attempt %s/%s", resp.status_code, attempt + 1, MAX_RETRIES)
                time.sleep(RETRY_BACKOFF ** attempt)
                continue
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            logger.warning("Fetch failed (attempt %s/%s): %s", attempt + 1, MAX_RETRIES, e)
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF ** attempt)
            else:
                logger.error("Fetch failed after %s attempts", MAX_RETRIES)
                return None
    return None
