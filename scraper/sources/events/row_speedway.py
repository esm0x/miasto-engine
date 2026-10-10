"""ROW Rybnik speedway fixtures, row.rybnik.com.pl/druzyna/terminarz. Rybnik only."""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timedelta
from typing import Callable, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from engine.common import PL_MONTHS, UA, Ctx, clean_text
from modules.events import (
    TIMEOUT,
    VALID_CATEGORIES,
    Event,
    classify,
    detect_venue,
    get_soup,
    http_get,
    iso,
    normalise_title,
    parse_iso_local,
    slugify,
)


# Source 5: ROW Rybnik speedway
# --------------------------------------------------------------------------- #

ROW_URL = "https://row.rybnik.com.pl/druzyna/terminarz"
ROW_VENUE = "Stadion Miejski w Rybniku, ul. Gliwicka 72"
ROW_DATE_RX = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})\s*(?:(\d{1,2})[:.](\d{2}))?")


def scrape_row() -> list[Event]:
    """Speedway fixtures. Season-bound: an empty table off-season is fine."""
    soup = get_soup(ROW_URL)
    events: list[Event] = []
    for row in soup.select("table tr"):
        date_cell = row.select_one("td.timetable + td.timetable") or None
        teams = [clean_text(td.get_text(" ", strip=True)) or "" for td in row.select("td.timetable-team")]
        if not date_cell or len(teams) < 2:
            continue
        m = ROW_DATE_RX.search(date_cell.get_text(" ", strip=True))
        if not m:
            continue
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        hour = int(m.group(4)) if m.group(4) else 0
        minute = int(m.group(5)) if m.group(5) else 0
        try:
            start = datetime(year, month, day, hour, minute)
        except ValueError:
            continue
        host, guest = teams[0], teams[1]
        home = "rybnik" in host.lower()
        title = f"Żużel: {host} – {guest}"
        round_cell = row.select_one("td.timetable")
        rnd = slugify(round_cell.get_text(" ", strip=True)) if round_cell else "runda"
        events.append(Event(
            id=f"row-{rnd}-{start:%Y%m%d}",
            title=title,
            category="Sport",
            start=iso(start),
            end=None,
            venue=ROW_VENUE if home else f"wyjazd: {host}",
            description=f"Mecz {'domowy' if home else 'wyjazdowy'} żużlowej ligi — {host} kontra {guest}.",
            sourceName="ROW Rybnik",
            sourceUrl=ROW_URL,
        ))
    print(f"[info] ROW: {len(events)} fixtures in the table", file=sys.stderr)
    return events


def fetch(params: dict, ctx: Ctx) -> list[Event]:
    return scrape_row()
