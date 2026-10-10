"""Events from an IDcom municipal portal (see sources/idcom.py).

Params:
    {"name": "lubomia.pl", "base": "https://lubomia.pl", "prefix": "lub",
     "months": 3}        # this month and the next two

The monthly list /wydarzenia/lista/<rok>/<miesiąc> gives the tiles; the detail page
gives the hours ("od 16:30 do 21:00"), the place and the portal's own category, which
goes to classify() as a hint.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from engine.common import Ctx, log
from modules.events import Event, classify, detect_venue, iso, slugify
from sources import idcom


def months_from(today: date, count: int) -> list[tuple[int, int]]:
    out = []
    y, m = today.year, today.month
    for _ in range(count):
        out.append((y, m))
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def parse_detail(url: str, name: str, prefix: str, city: str) -> Optional[Event]:
    page = idcom.soup(url)
    title = idcom.meta(page, "og:title")
    when_el = page.select_one(".article__metatags_when")
    start, end = idcom.parse_when(when_el.get_text(" ", strip=True)) if when_el else (None, None)
    if not title or not start:
        log(f"[warn] {name}: no title or date at {url}")
        return None
    loc_el = page.select_one(".article__metatags_localization")
    place = idcom.venue_from_location(loc_el.get_text(" ", strip=True)) if loc_el else None
    lead = idcom.meta(page, "og:description")
    # "Organizator: Gmina Lubomia" alone is not a description.
    description = None if not lead or lead.lower().startswith("organizator:") and len(lead) < 60 else lead
    cat_el = page.select_one(".article__metatags_category")
    hint = cat_el.get_text(" ", strip=True) if cat_el else None
    venue = place or detect_venue(f"{title} {description or ''}", city) or city
    event_id = url.rstrip("/").split("/wydarzenia/", 1)[-1].split("/", 1)[0]
    return Event(
        id=f"{prefix}-{event_id}-{slugify(title, 50)}",
        title=title,
        category=classify(title, description, hint, venue),
        start=iso(start),
        end=iso(end) if end and end > start else None,
        venue=venue,
        description=description,
        sourceName=name,
        sourceUrl=url,
    )


def fetch(params: dict, ctx: Ctx) -> list[Event]:
    name = params.get("name") or params["base"].split("//", 1)[-1]
    base = params["base"].rstrip("/")
    prefix = params.get("prefix", ctx.slug)
    urls: list[str] = []
    for year, month in months_from(ctx.today, int(params.get("months", 3))):
        for url in idcom.detail_links(idcom.soup(f"{base}/wydarzenia/lista/{year}/{month}"), base, "wydarzenia"):
            if url not in urls:
                urls.append(url)
        idcom.polite()
    log(f"[info] {name}: {len(urls)} wydarzeń na liście")

    events: list[Event] = []
    for url in urls:
        try:
            ev = parse_detail(url, name, prefix, ctx.name)
            if ev:
                events.append(ev)
        except Exception as e:  # noqa: BLE001 — one broken page is not fatal
            log(f"[warn] {name} {url}: {e}")
        idcom.polite()
    return events
