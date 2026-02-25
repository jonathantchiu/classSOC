"""Parser: extract section statuses from UCLA SOC HTML."""

import logging
import re
from datetime import datetime, timezone
from typing import Optional

from bs4 import BeautifulSoup

from .models import Snapshot, Status

logger = logging.getLogger(__name__)

# Normalize raw status text to enum
STATUS_MAP = {
    "open": Status.OPEN,
    "closed": Status.CLOSED,
    "full": Status.CLOSED,
    "closed by dept": Status.CLOSED,
    "waitlist": Status.WAITLISTED,
    "waitlisted": Status.WAITLISTED,
    "cancelled": Status.CANCELLED,
    "canceled": Status.CANCELLED,
}

# UCLA SOC status phrases (order matters for regex)
STATUS_PHRASES = [
    "closed by dept",
    "waitlisted",
    "waitlist",
    "cancelled",
    "canceled",
    "open",
    "closed",
    "full",
]


def _normalize(raw_text: str) -> Status:
    """Map raw status text to normalized Status enum."""
    key = raw_text.strip().lower()
    return STATUS_MAP.get(key, Status.UNKNOWN)


def parse(html: str) -> Optional[Snapshot]:
    """
    Parse HTML into Snapshot. Best-effort, defensive.
    Returns None on parse failure; logs errors.
    """
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception as e:
        logger.error("Failed to parse HTML: %s", e)
        return None

    sections: dict[str, str] = {}
    raw: dict[str, str] = {}
    meta: Optional[dict[str, str]] = None

    rows = _find_ucla_soc_rows(soup)
    if not rows:
        # Fallback: try legacy table structure (for fixtures)
        rows = _find_legacy_table_rows(soup)

    if not rows:
        logger.warning("No section rows found; SOC HTML structure may have changed")

    for row in rows:
        label, raw_status = _extract_ucla_row(row)
        if not label or not raw_status:
            label, raw_status = _extract_legacy_row(row)
        if label and raw_status:
            sections[label] = _normalize(raw_status).value
            raw[label] = raw_status

    return Snapshot(
        timestamp=datetime.now(timezone.utc),
        sections=sections,
        raw=raw if raw else None,
        meta=meta,
    )


def _find_ucla_soc_rows(soup: BeautifulSoup) -> list:
    """Find UCLA SOC data rows: div.row-fluid.data_row with sectionColumn."""
    rows = []
    for row in soup.find_all("div", class_=re.compile(r"data_row")):
        if row.find("div", class_="sectionColumn") and row.find("div", class_="statusColumn"):
            rows.append(row)
    return rows


def _extract_ucla_row(row) -> tuple[Optional[str], Optional[str]]:
    """Extract (label, raw_status) from UCLA SOC row structure."""
    section_col = row.find("div", class_="sectionColumn")
    status_col = row.find("div", class_="statusColumn")
    if not section_col or not status_col:
        return None, None

    # Section label: from <a> or div inside .cls-section (e.g. "Lec 1", "Dis 1A")
    # Note: get_text() can be empty on some SOC pages; use .string or regex fallback
    label = None
    cls_section = section_col.find("div", class_="cls-section")
    if cls_section:
        a = cls_section.find("a")
        if a:
            label = a.get_text(strip=True) or (a.string.strip() if a.string else None)
        if not label:
            text = cls_section.get_text(strip=True) or cls_section.decode_contents()
            match = re.search(r"(Lec|Dis|Lab|Sem)\s*\d\w*", text, re.I)
            label = match.group(0) if match else None

    if not label or not re.match(r"^(Lec|Dis|Lab|Sem)\s*\d", label, re.I):
        return None, None

    # Status: from statusColumn <p>, extract status phrase
    # (BeautifulSoup get_text can be empty on some SOC pages; use regex fallback)
    status_p = status_col.find("p")
    if not status_p:
        return label, "UNKNOWN"

    text = status_p.get_text(separator=" ", strip=True)
    if not text:
        # Fallback: regex on raw HTML (handles SOC page structure)
        inner = status_col.decode_contents()
        raw_status = _extract_status_from_html(inner)
    else:
        raw_status = _extract_status_from_text(text)
    return label, raw_status


def _extract_status_from_text(text: str) -> str:
    """Extract status phrase from status column text (e.g. 'Closed by Dept Computer Science (0 capacity...)')."""
    # Remove capacity parenthetical
    text = re.sub(r"\s*\([^)]*capacity[^)]*\).*", "", text, flags=re.I).strip()
    text_lower = text.lower()
    for phrase in STATUS_PHRASES:
        if phrase in text_lower:
            # Return with original casing from first occurrence
            idx = text_lower.find(phrase)
            return text[idx : idx + len(phrase)]
    return "UNKNOWN"


def _extract_status_from_html(html: str) -> str:
    """Extract status phrase from status column HTML (fallback when get_text is empty)."""
    match = re.search(
        r"\b(Open|Closed by Dept|Full|Waitlisted|Cancelled|Canceled|Waitlist|Closed)\b",
        html,
        re.I,
    )
    return match.group(1) if match else "UNKNOWN"


def _find_legacy_table_rows(soup: BeautifulSoup) -> list:
    """Legacy: table rows for fixtures."""
    rows = []
    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            cells = tr.find_all(["td", "th"])
            if len(cells) >= 2:
                rows.append(tr)
    return rows


def _extract_legacy_row(row) -> tuple[Optional[str], Optional[str]]:
    """Legacy: extract from table cells (for fixtures)."""
    cells = row.find_all(["td", "th"])
    if len(cells) < 2:
        return None, None
    label_candidate = cells[0].get_text(strip=True)
    status_candidate = cells[-1].get_text(strip=True)
    if status_candidate.isdigit() and len(cells) >= 3:
        status_candidate = cells[-2].get_text(strip=True)
    if not re.match(r"^(Lec|Dis|Lab|Sem)\s*\d", label_candidate, re.I):
        return None, None
    return label_candidate, status_candidate
