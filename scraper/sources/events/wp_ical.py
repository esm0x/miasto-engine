"""WordPress sites running The Events Calendar: <listing>?ical=1, HTML fallback.

Most domy kultury use this plugin, so this is the parser to try first for a new town.

Params: {"name": "DK Boguszowice", "url": "https://.../wydarzenia/", "prefix": "dk-bog",
         "venue": "Dom Kultury Boguszowice", "htmlFallback": null | "dkchwalowice" | "dkniedobczyce"}"""

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


# Source 4: Domy Kultury — iCal first, HTML fallback
# --------------------------------------------------------------------------- #

def unfold_ics(text: str) -> list[str]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out: list[str] = []
    for line in lines:
        if line[:1] in (" ", "\t") and out:
            out[-1] += line[1:]
        else:
            out.append(line)
    return out


def ics_unescape(value: str) -> str:
    return (value.replace("\\n", "\n").replace("\\N", "\n")
                 .replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\"))


def parse_ics(text: str) -> list[dict[str, tuple[str, str]]]:
    """Minimal VEVENT reader → [{KEY: (value, raw_params)}]."""
    events: list[dict[str, tuple[str, str]]] = []
    current: Optional[dict[str, tuple[str, str]]] = None
    for line in unfold_ics(text):
        stripped = line.strip()
        if stripped == "BEGIN:VEVENT":
            current = {}
        elif stripped == "END:VEVENT":
            if current is not None:
                events.append(current)
            current = None
        elif current is not None and ":" in line:
            name, _, value = line.partition(":")
            key, _, params = name.partition(";")
            current[key.strip().upper()] = (value, params)
    return events


def parse_ics_dt(value: str, params: str) -> datetime:
    v = value.strip()
    if "VALUE=DATE" in params.upper() or len(v) == 8:
        return datetime.strptime(v[:8], "%Y%m%d")
    if v.endswith("Z"):
        dt = datetime.strptime(v, "%Y%m%dT%H%M%SZ")
        try:
            from zoneinfo import ZoneInfo
            return dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("Europe/Warsaw")).replace(tzinfo=None)
        except Exception:  # noqa: BLE001 — no tzdata on the runner
            return dt + timedelta(hours=2)
    return datetime.strptime(v[:15], "%Y%m%dT%H%M%S")




def parse_dk_ical(source: str, url: str, prefix: str, default_venue: str) -> list[Event]:
    """The Events Calendar exposes <listing>?ical=1. Returns [] if it does not."""
    sep = "&" if "?" in url else "?"
    r = requests.get(f"{url}{sep}ical=1", headers={"User-Agent": UA}, timeout=TIMEOUT)
    if r.status_code != 200 or "text/calendar" not in r.headers.get("content-type", ""):
        return []
    text = r.content.decode("utf-8", errors="replace")
    events: list[Event] = []
    for raw in parse_ics(text):
        if "DTSTART" not in raw or "SUMMARY" not in raw:
            continue
        title = clean_text(ics_unescape(raw["SUMMARY"][0]))
        if not title:
            continue
        start = parse_ics_dt(*raw["DTSTART"])
        end = parse_ics_dt(*raw["DTEND"]) if "DTEND" in raw else None
        description = clean_text(ics_unescape(raw["DESCRIPTION"][0])) if "DESCRIPTION" in raw else None
        link = (raw.get("URL") or (url, ""))[0].strip() or url
        hint = ics_unescape(raw["CATEGORIES"][0]) if "CATEGORIES" in raw else ""
        venue = detect_venue(f"{title} {description or ''}", default_venue) or default_venue
        uid = (raw.get("UID") or ("", ""))[0].split("@")[0].split("-")[0]
        events.append(Event(
            id=f"{prefix}-{slugify(uid + '-' + title, 70)}",
            title=title,
            category=classify(title, description, hint, venue),
            start=iso(start),
            end=iso(end) if end else None,
            venue=venue,
            description=description,
            sourceName=source,
            sourceUrl=link,
        ))
    return events


def parse_dkchwalowice_html(source: str, url: str, prefix: str, default_venue: str) -> list[Event]:
    """Fallback: the news grid, where dated items carry '| DD.MM.YYYY' in the title."""
    soup = get_soup(url)
    events: list[Event] = []
    for block in soup.select("div.news"):
        link = block.select_one(".title a[href]")
        if not link:
            continue
        title_raw = clean_text(link.get_text(" ", strip=True)) or ""
        body = block.select_one(".header")
        description = clean_text(body.get_text(" ", strip=True)) if body else None
        blob = f"{title_raw} {description or ''}"

        m = re.search(r"\|\s*(\d{1,2})\.(\d{1,2})\.(\d{4})", title_raw)
        if m:
            day, month, year = (int(x) for x in m.groups())
        else:
            m2 = re.search(r"(\d{1,2})\s+([a-ząćęłńóśźż]+)\s+(\d{4})", blob, re.IGNORECASE)
            if not m2 or m2.group(2).lower() not in PL_MONTHS:
                continue
            day, month, year = int(m2.group(1)), PL_MONTHS[m2.group(2).lower()], int(m2.group(3))
        tm = re.search(r"(?:godz\.\s*|\bo\s+)(\d{1,2})[:.](\d{2})", blob)
        hour, minute = (int(tm.group(1)), int(tm.group(2))) if tm else (0, 0)
        try:
            start = datetime(year, month, day, hour, minute)
        except ValueError:
            continue

        title = re.sub(r"\s*\|\s*\d{1,2}\.\d{1,2}\.\d{4}\s*$", "", title_raw).strip()
        venue = detect_venue(blob, default_venue) or default_venue
        events.append(Event(
            id=f"{prefix}-{slugify(title)}-{start:%Y%m%d}",
            title=title,
            category=classify(title, description, source, venue),
            start=iso(start),
            end=None,
            venue=venue,
            description=description,
            sourceName=source,
            sourceUrl=urljoin(url, link["href"]),
        ))
    return events


def parse_dkniedobczyce_html(source: str, url: str, prefix: str, default_venue: str) -> list[Event]:
    """Fallback: the /terminarz/ table (Nazwa | Data | Uwagi)."""
    soup = get_soup(url)
    events: list[Event] = []
    for row in soup.select("table tr"):
        cells = [clean_text(td.get_text(" ", strip=True)) or "" for td in row.find_all("td")]
        if len(cells) < 2:
            continue
        title, date_cell = cells[0], cells[1]
        m = re.search(r"(\d{1,2})(?:-\d{1,2})?\.(\d{1,2})\.(\d{4})", date_cell)
        if not title or not m:
            continue
        try:
            start = datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            continue
        note = cells[2] if len(cells) > 2 else None
        venue = detect_venue(f"{title} {note or ''}", default_venue) or default_venue
        events.append(Event(
            id=f"{prefix}-{slugify(title)}-{start:%Y%m%d}",
            title=title,
            category=classify(title, note, source, venue),
            start=iso(start),
            end=None,
            venue=venue,
            description=note,
            sourceName=source,
            sourceUrl=url,
        ))
    return events


# Named by params["htmlFallback"] for sites whose iCal export is switched off.
DK_HTML_FALLBACKS = {
    "dkchwalowice": parse_dkchwalowice_html,
    "dkniedobczyce": parse_dkniedobczyce_html,
}


def make_dk_scraper(
    source: str, url: str, prefix: str, venue: str, fallback_name: Optional[str] = None,
) -> Callable[[], list[Event]]:
    def scrape() -> list[Event]:
        events = parse_dk_ical(source, url, prefix, venue)
        if events:
            print(f"[info] {source}: {len(events)} events from iCal", file=sys.stderr)
            return events
        fallback = DK_HTML_FALLBACKS.get(fallback_name or "")
        if not fallback:
            return []
        events = fallback(source, url, prefix, venue)
        print(f"[info] {source}: no iCal, {len(events)} events from HTML", file=sys.stderr)
        return events
    scrape.__name__ = f"scrape_{prefix.replace('-', '_')}"
    return scrape


def fetch(params: dict, ctx: Ctx) -> list[Event]:
    return make_dk_scraper(
        params["name"], params["url"], params["prefix"], params["venue"], params.get("htmlFallback"),
    )()
