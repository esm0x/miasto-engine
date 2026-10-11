"""Events from a TYPO3 city calendar that feeds its widget from a JSON list (zory.pl).

Params:
    {"name": "zory.pl", "base": "https://www.zory.pl", "json": "/json/", "prefix": "zory"}

The calendar page draws itself in the browser from base + json: a list of
{"text": "<p><a href='/…/wydarzenie/slug'>Title</a></p>", "start": ISO, "end": ISO}
with the offset already Europe/Warsaw. The detail page adds the description
(.teaser-text) and the place (.event-location [itemprop=name]).
"""

from __future__ import annotations

import json
import time
from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from engine.common import Ctx, clean_text, log, same_site, truncate
from modules.events import Event, classify, detect_venue, get_soup, http_get, iso, parse_iso_local, slugify

POLITE = 0.5


def parse_list(raw: str, base: str) -> list[dict]:
    """[{title, url, start, end}] from the widget's JSON; entries without a link are skipped."""
    host = urlparse(base).hostname or ""
    out = []
    for e in json.loads(raw):
        a = BeautifulSoup(e.get("text") or "", "html.parser").find("a", href=True)
        if not a or not e.get("start"):
            continue
        url = urljoin(base, a["href"])
        if not same_site(url, host.removeprefix("www.")):
            continue
        out.append({"title": clean_text(a.get_text(" ", strip=True)), "url": url,
                    "start": parse_iso_local(e["start"]),
                    "end": parse_iso_local(e["end"]) if e.get("end") else None})
    return out


def detail(url: str) -> tuple[Optional[str], Optional[str]]:
    """(description, place) from the event page; either may be missing."""
    page = get_soup(url)
    teaser = page.select_one(".teaser-text")
    place = page.select_one(".event-location [itemprop=name]")
    return (clean_text(teaser.get_text(" ", strip=True)) if teaser else None,
            clean_text(place.get_text(" ", strip=True)) if place else None)


def fetch(params: dict, ctx: Ctx) -> list[Event]:
    name = params.get("name") or params["base"].split("//", 1)[-1]
    base = params["base"].rstrip("/") + "/"
    prefix = params.get("prefix", ctx.slug)
    entries = parse_list(http_get(urljoin(base, params.get("json", "/json/"))), base)
    log(f"[info] {name}: {len(entries)} wydarzeń w kalendarzu")
    today = ctx.today
    events: list[Event] = []
    for e in entries:
        last_day = (e["end"] or e["start"]).date()
        if last_day < today:
            continue
        try:
            description, place = detail(e["url"])
        except Exception as ex:  # noqa: BLE001 — the list alone still makes an event
            log(f"[warn] {name} {e['url']}: {ex}")
            description, place = None, None
        time.sleep(POLITE)
        title = e["title"]
        if not title:
            continue
        # One page with a novel in its teaser must not break the contract for the file.
        description = truncate(description, 1000) if description else None
        venue = place or detect_venue(f"{title} {description or ''}", ctx.name) or ctx.name
        start, end = e["start"], e["end"]
        events.append(Event(
            id=f"{prefix}-{slugify(e['url'].rstrip('/').rsplit('/', 1)[-1], 50)}",
            title=title,
            category=classify(title, description, None, venue),
            start=iso(start),
            end=iso(end) if end and end > start else None,
            venue=venue,
            description=description,
            sourceName=name,
            sourceUrl=e["url"],
        ))
    return events
