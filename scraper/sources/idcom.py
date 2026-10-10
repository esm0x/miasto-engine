"""Shared pieces of the IDcom "CMS-GOV" municipal portal (cms-v2-files.idcom-jst.pl).

IDcom runs the websites of many Polish gminas on one engine, Lubomia's among them
(sites/158). The URLs and markup are the same everywhere, so these parsers are written
against the engine, not the town: a new IDcom gmina needs only its base URL and its
category ids in sources.json.

Recognise an IDcom site by "cms-v2-files.idcom-jst.pl" in image URLs, and by the paths
/wiadomosci/kategoria/<id> and /wydarzenia/lista/<rok>/<miesiąc>.

What the engine gives and what it does not, verified on lubomia.pl (October 2026):
  * no RSS, no API, no JSON-LD; everything is server-rendered HTML;
  * list tiles carry the title cut at ~60 characters with "...", and news tiles carry
    no date at all, so every item needs its detail page;
  * the detail page has the full title in og:title, a lead in og:description, and the
    date in prose: "15 września 2026 godz. 12:40";
  * an event's "Kiedy" reads "23 października 2026 od 16:30 do 21:00", or a range
    "26 września 2026 - 28 września 2026" with no hours.
"""

from __future__ import annotations

import re
import time
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from engine.common import PL_MONTHS, UA, clean_text, get

HEADERS = {"User-Agent": UA, "Accept-Language": "pl-PL,pl;q=0.9"}
POLITE_DELAY = 0.3

DATE_RX = re.compile(r"(\d{1,2})\s+([a-ząćęłńóśźż]+)\s+(\d{4})", re.IGNORECASE)
TIME_RX = re.compile(r"(\d{1,2}):(\d{2})")


def soup(url: str) -> BeautifulSoup:
    return BeautifulSoup(get(url, headers=HEADERS, retries=2).text, "html.parser")


def polite() -> None:
    time.sleep(POLITE_DELAY)


def meta(page: BeautifulSoup, prop: str) -> Optional[str]:
    el = page.select_one(f'meta[property="{prop}"]') or page.select_one(f'meta[name="{prop}"]')
    return clean_text(el.get("content")) if el and el.get("content") else None


def detail_links(page: BeautifulSoup, base: str, kind: str) -> list[str]:
    """Unique detail URLs on a list page, in page order. kind: wiadomosci | wydarzenia."""
    out: list[str] = []
    for a in page.select("a.tile__title[href], a[href]"):
        href = a.get("href", "")
        # Relative, or absolute on the portal itself; never a link out.
        if re.match(rf"^(?:{re.escape(base)})?/{kind}/\d+/", href):
            url = urljoin(base, href)
            if url not in out:
                out.append(url)
    return out


def parse_date(text: str) -> Optional[datetime]:
    """'15 września 2026 godz. 12:40' → datetime; the first date in the text wins."""
    m = DATE_RX.search(text or "")
    if not m:
        return None
    month = PL_MONTHS.get(m.group(2).lower())
    if not month:
        return None
    rest = text[m.end():]
    t = TIME_RX.search(rest)
    hour, minute = (int(t.group(1)), int(t.group(2))) if t else (0, 0)
    try:
        return datetime(int(m.group(3)), month, int(m.group(1)), hour, minute)
    except ValueError:
        return None


def parse_when(text: str) -> tuple[Optional[datetime], Optional[datetime]]:
    """An event's "Kiedy": start, and the end when the page gives one.

    '23 października 2026 od 16:30 do 21:00' → 16:30 and 21:00 the same day;
    '26 września 2026 - 28 września 2026'    → the two days, no hours.
    """
    text = " ".join((text or "").split())
    dates = list(DATE_RX.finditer(text))
    if not dates:
        return None, None
    start = parse_date(text[dates[0].start():])
    if start is None:
        return None, None
    hours = re.search(r"od\s+(\d{1,2}):(\d{2})(?:\s+do\s+(\d{1,2}):(\d{2}))?", text)
    end: Optional[datetime] = None
    if hours:
        start = start.replace(hour=int(hours.group(1)), minute=int(hours.group(2)))
        if hours.group(3):
            end = start.replace(hour=int(hours.group(3)), minute=int(hours.group(4)))
    if len(dates) > 1:
        end = parse_date(text[dates[1].start():]) or end
    return start, end


ADMIN_PREFIX_RX = re.compile(
    r"^(?:województwo\s+[^,]+,\s*)?(?:powiat\s+[^,]+,\s*)?(?:gmina\s+[^,]+,\s*)?", re.IGNORECASE,
)
POSTCODE_TAIL_RX = re.compile(r",?\s*\d{2}-\d{3}\s+[^,]+$")


def venue_from_location(text: str) -> Optional[str]:
    """'Województwo śląskie, powiat wodzisławski, gmina Lubomia, Nieboczowy, Wiejski
    Dom Kultury … ul. Wiejska 25, Nieboczowy, 44-360 Lubomia' → 'Wiejski Dom Kultury …
    ul. Wiejska 25, Nieboczowy'. The administrative chain says nothing a resident needs.
    """
    text = clean_text(re.sub(r"^\s*Lokalizacja\s*-?\s*", "", text or "", flags=re.IGNORECASE)) or ""
    text = ADMIN_PREFIX_RX.sub("", text)
    # After the chain the village comes first on its own ("Nieboczowy, Wiejski Dom…").
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if len(parts) > 2 and len(parts[0].split()) == 1:
        parts = parts[1:]
    venue = ", ".join(parts)
    venue = POSTCODE_TAIL_RX.sub("", venue).strip(" ,")
    return venue or None
