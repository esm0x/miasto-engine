"""Hand-maintained events from cities/<slug>/manual_events.json.

Params: {"file": "manual_events.json"} (relative to the city directory, optional)."""

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


# --------------------------------------------------------------------------- #

# cities/<slug>/manual_events.json, set per call.
MANUAL_PATH = None


def scrape_manual() -> list[Event]:
    """Hand-maintained events, merged in like any other source.

    Some venues — Klub NOC and Szepty above all — publish only to Facebook, and there
    is no lawful machine-readable feed for them (Meta removed the Page events API, and
    every ticketing platform lists the venues with zero events). Rather than scrape Meta,
    those go in cities/<slug>/manual_events.json by hand. This reader never writes that file.
    """
    if not MANUAL_PATH.exists():
        print("[info] no manual_events.json — skipping", file=sys.stderr)
        return []

    raw = json.loads(MANUAL_PATH.read_text(encoding="utf-8"))
    out: list[Event] = []
    for i, entry in enumerate(raw.get("events", []), 1):
        title = (entry.get("title") or "").strip()
        start = (entry.get("start") or "").strip()
        venue = (entry.get("venue") or "").strip()
        if not (title and start and venue):
            print(f"[warn] manual #{i}: brak title/start/venue — pomijam", file=sys.stderr)
            continue
        try:
            datetime.fromisoformat(start)
        except ValueError:
            print(f"[warn] manual #{i} ({title!r}): zla data {start!r} — pomijam", file=sys.stderr)
            continue

        category = (entry.get("category") or "Inne").strip()
        if category not in VALID_CATEGORIES:
            print(f"[warn] manual #{i} ({title!r}): nieznana kategoria {category!r} "
                  f"— ustawiam Inne", file=sys.stderr)
            category = "Inne"

        out.append(Event(
            id=f"manual-{slugify(title)}-{start[:10]}",
            title=title,
            category=category,
            start=start,
            end=(entry.get("end") or None),
            venue=venue,
            description=(entry.get("description") or None),
            sourceName=venue,
            sourceUrl=(entry.get("sourceUrl") or ""),
        ))

    print(f"[info] manual: {len(out)} wydarzen", file=sys.stderr)
    return out


def fetch(params: dict, ctx: Ctx) -> list[Event]:
    global MANUAL_PATH
    MANUAL_PATH = ctx.input_file(params.get("file", "manual_events.json"))
    return scrape_manual()
