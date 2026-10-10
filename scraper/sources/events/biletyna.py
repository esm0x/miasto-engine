"""biletyna.pl/<Miasto>: schema.org JSON-LD ItemList.

Params: {"url": "https://biletyna.pl/Rybnik"}. Works for any town biletyna lists."""

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


# Source 3: biletyna.pl — schema.org JSON-LD
# --------------------------------------------------------------------------- #

# Set per call from params["url"]: biletyna.pl has a page per town.
BILETYNA_URL = ""
CITY = ""

# schema.org subtype → hint word fed to classify()
BILETYNA_TYPE_HINT = {
    "MusicEvent": "koncert",
    "TheaterEvent": "spektakl",
    "ScreeningEvent": "film seans",
    "ChildrensEvent": "dla dzieci",
    "ComedyEvent": "kabaret",
    "DanceEvent": "impreza taneczna",
    "Festival": "festiwal",
    "ExhibitionEvent": "wystawa",
    "SportsEvent": "mecz sport",
    "EducationEvent": "warsztaty",
}

# biletyna appends a boilerplate sentence to every description
BILETYNA_BOILERPLATE = re.compile(
    r"\s*Wydarzenie odbędzie się w .*?(?:o godz\.\s*\d{1,2}[:.]\d{2})\.?\s*$", re.IGNORECASE
)


def biletyna_ld_items(soup: BeautifulSoup) -> list[dict]:
    items: list[dict] = []
    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.string or script.get_text()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"[warn] biletyna: bad JSON-LD ({e})", file=sys.stderr)
            continue
        if isinstance(data, dict) and data.get("@type") == "ItemList":
            for entry in data.get("itemListElement", []):
                item = entry.get("item") if isinstance(entry, dict) else None
                if isinstance(item, dict) and item.get("startDate"):
                    items.append(item)
    return items


def parse_biletyna_item(item: dict) -> Optional[Event]:
    title = clean_text(item.get("name"))
    start_raw = item.get("startDate")
    if not title or not start_raw:
        return None
    start = parse_iso_local(start_raw)
    end = parse_iso_local(item["endDate"]) if item.get("endDate") else None

    location = item.get("location") or {}
    venue = clean_text(location.get("name")) if isinstance(location, dict) else None
    address = location.get("address") if isinstance(location, dict) else None
    street = clean_text(address.get("streetAddress")) if isinstance(address, dict) else None
    if venue and street:
        venue = f"{venue}, {street}"
    venue = venue or detect_venue(title, CITY) or CITY

    description = clean_text(item.get("description"))
    if description:
        description = clean_text(BILETYNA_BOILERPLATE.sub("", description))

    hint = BILETYNA_TYPE_HINT.get(str(item.get("@type")), "")
    url = item.get("url") or BILETYNA_URL

    return Event(
        id=f"bilnya-{slugify(title)}-{start:%Y%m%d%H%M}",
        title=title,
        category=classify(title, description, hint, venue),
        start=iso(start),
        end=iso(end) if end else None,
        venue=venue,
        description=description,
        sourceName="biletyna.pl",
        sourceUrl=url,
    )


def scrape_biletyna() -> list[Event]:
    session = requests.Session()
    seen: dict[tuple[str, str], Event] = {}
    empty_pages = 0
    # Paging on biletyna is server-side and a bit stateful: identical requests can
    # return the same slice a few times before it advances. Walk a handful of pages
    # and stop once nothing new shows up.
    for page in range(1, 9):
        url = BILETYNA_URL if page == 1 else f"{BILETYNA_URL}?page={page}"
        soup = BeautifulSoup(http_get(url, session), "html.parser")
        items = biletyna_ld_items(soup)
        new = 0
        for item in items:
            ev = parse_biletyna_item(item)
            if not ev:
                continue
            key = (normalise_title(ev.title), ev.start)
            if key not in seen:
                seen[key] = ev
                new += 1
        print(f"[info] biletyna: page {page} → {len(items)} items, {new} new", file=sys.stderr)
        empty_pages = empty_pages + 1 if new == 0 else 0
        if empty_pages >= 3:
            break
        time.sleep(0.4)
    return list(seen.values())


def fetch(params: dict, ctx: Ctx) -> list[Event]:
    global BILETYNA_URL, CITY
    BILETYNA_URL = params["url"]
    CITY = ctx.name
    return scrape_biletyna()
