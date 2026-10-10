"""iRybnik, irybnik.pl/wydarzenie: HTML list plus per-event JSON-LD. Rybnik only."""

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


# Source 2: iRybnik — the nightlife/gig feed
# --------------------------------------------------------------------------- #

IRYBNIK_BASE = "https://irybnik.pl"
IRYBNIK_LIST_URL = f"{IRYBNIK_BASE}/wydarzenie/"


def irybnik_ld_events(soup: BeautifulSoup) -> list[dict]:
    """All schema.org Event objects embedded in a page (list or detail)."""
    out: list[dict] = []
    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.string or script.get_text()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        blobs = data if isinstance(data, list) else [data]
        for blob in blobs:
            if not isinstance(blob, dict):
                continue
            if blob.get("@type") == "ItemList":
                for item in blob.get("itemListElement", []):
                    inner = item.get("item") if isinstance(item, dict) else None
                    if isinstance(inner, dict) and "Event" in str(inner.get("@type", "")):
                        out.append(inner)
            elif "Event" in str(blob.get("@type", "")):
                out.append(blob)
    return out


def irybnik_collect_listings(soup: BeautifulSoup) -> list[dict]:
    """Every event row on the listing page (cards = upcoming, month sections also
    contain past ones — those get dropped by the future filter later)."""
    rows: dict[str, dict] = {}
    for art in soup.select("article.event-card, article.event-item"):
        link = art.select_one("a.event-link[href]")
        time_el = art.select_one("time[datetime]")
        if not link or not time_el:
            continue
        url = urljoin(IRYBNIK_BASE, link["href"])
        desc = art.select_one(".event-description")
        rows.setdefault(url, {
            "url": url,
            "title": clean_text(link.get_text(" ", strip=True)) or "",
            "start": time_el["datetime"],
            "description": clean_text(desc.get_text(" ", strip=True)) if desc else None,
        })
    return list(rows.values())


def irybnik_venue(ld: dict, title: str, description: str) -> str:
    location = ld.get("location") or {}
    address = clean_text(location.get("name")) if isinstance(location, dict) else None
    organizer = ld.get("organizer") or {}
    org = clean_text(organizer.get("name")) if isinstance(organizer, dict) else None
    if org:
        org = re.sub(r"\s*[-–]\s*(wydarzenia|events)$", "", org, flags=re.IGNORECASE)

    name = detect_venue(f"{title} {description} {address or ''}") or (
        org if org and org.lower() not in ("rybnik", "irybnik", "irybnik.pl") else None
    )
    if address and address.strip().lower() in ("rybnik", "pl", ""):
        address = None
    if name and address and normalise_title(name) not in normalise_title(address):
        return f"{name}, {address}"
    return name or address or "Rybnik"


def parse_irybnik_detail(row: dict, session: requests.Session) -> Event:
    """Enrich a listing row with the detail page (full text + real address)."""
    title = row["title"]
    description = row.get("description")
    venue = None
    try:
        soup = BeautifulSoup(http_get(row["url"], session), "html.parser")
        body = soup.select_one("article.article-content")
        if body:
            paragraphs = [
                t for p in body.find_all("p")
                if (t := p.get_text(" ", strip=True))
                and len(t) >= 40
                and not t.lower().startswith(("autor:", "link do wydarzenia"))
            ]
            full = " ".join(paragraphs[:4])
            if full and len(full) > len(description or ""):
                description = clean_text(full)[:1500]
        lds = irybnik_ld_events(soup)
        if lds:
            venue = irybnik_venue(lds[0], title, description or "")
            if lds[0].get("startDate"):
                row["start"] = lds[0]["startDate"]
    except Exception as e:  # noqa: BLE001 — fall back to the listing data
        print(f"[warn] iRybnik detail {row['url']}: {e}", file=sys.stderr)

    if not venue:
        venue = detect_venue(f"{title} {description or ''}", "Rybnik") or "Rybnik"
    start = parse_iso_local(row["start"])
    return Event(
        id="iryb-" + slugify(row["url"].rstrip("/").split("/")[-1]),
        title=title,
        category=classify(title, description, "iRybnik", venue),
        start=iso(start),
        end=None,
        venue=venue,
        description=description,
        sourceName="iRybnik",
        sourceUrl=row["url"],
    )


def scrape_irybnik() -> list[Event]:
    session = requests.Session()
    print(f"[info] iRybnik: fetching {IRYBNIK_LIST_URL}", file=sys.stderr)
    soup = BeautifulSoup(http_get(IRYBNIK_LIST_URL, session), "html.parser")
    rows = irybnik_collect_listings(soup)

    # The month sections also list events that already happened; skip them here
    # so we do not fetch ~130 useless detail pages.
    cutoff = datetime.now() - timedelta(hours=3)
    rows = [r for r in rows if parse_iso_local(r["start"]) >= cutoff]
    print(f"[info] iRybnik: {len(rows)} upcoming listings", file=sys.stderr)

    events: list[Event] = []
    for i, row in enumerate(rows, 1):
        try:
            events.append(parse_irybnik_detail(row, session))
        except Exception as e:  # noqa: BLE001
            print(f"[error] iRybnik {row.get('url')}: {e}", file=sys.stderr)
        if i % 20 == 0:
            print(f"[info] iRybnik: {i}/{len(rows)}", file=sys.stderr)
        time.sleep(0.25)
    return events


def fetch(params: dict, ctx: Ctx) -> list[Event]:
    return scrape_irybnik()
