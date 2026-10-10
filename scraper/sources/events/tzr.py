"""Teatr Ziemi Rybnickiej, teatrziemirybnickiej.pl/wydarzenia: HTML detail pages.

No params: the theatre is its own source with its own markup."""

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


# Source 1: Teatr Ziemi Rybnickiej (unchanged logic, richer venue/category)
# --------------------------------------------------------------------------- #

TZR_BASE = "https://www.teatrziemirybnickiej.pl"
TZR_LIST_URL = f"{TZR_BASE}/wydarzenia"

# TZR prints its own category label above the <h1>; we forward it to classify()
# as a hint rather than trusting it blindly.
TZR_LABELS = (
    "koncert", "spektakl", "kabaret", "stand-up", "film", "festiwal", "wystawa",
    "warsztaty", "musical", "operetka", "opera", "balet", "widowisko", "taniec",
    "jam session", "dla dzieci", "wydarzenie plenerowe", "inne",
)

# Matches BOTH: "18.09.2026, godz. 19:00" AND "18.09.2026, godz. 19.00"
# (list page uses colon, detail page uses dot — go figure)
TZR_DATE_RX = re.compile(
    r"(\d{1,2})\.(\d{1,2})\.(\d{4})\s*,?\s*godz\.\s*(\d{1,2})[:\.](\d{2})",
    re.IGNORECASE,
)


def tzr_parse_dt(m: re.Match) -> datetime:
    d, mo, y, h, mi = m.groups()
    return datetime(int(y), int(mo), int(d), int(h), int(mi))


def tzr_collect_urls(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []
    seen: set[str] = set()
    for a in soup.select("a[href]"):
        href = a["href"]
        if "/wydarzenia/" not in href or not href.endswith(".html"):
            continue
        full = urljoin(TZR_BASE, href)
        if full.rstrip("/") == TZR_LIST_URL.rstrip("/"):
            continue
        if full in seen:
            continue
        seen.add(full)
        urls.append(full)
    return urls


def tzr_detect_label(soup: BeautifulSoup, h1) -> Optional[str]:
    """The category label sits in a plain text/element BEFORE the h1, e.g. 'Koncert'."""
    parts: list[str] = []
    for node in h1.find_all_previous(string=True, limit=40):
        s = node.strip()
        if s:
            parts.append(s.lower())
    haystack = " ".join(parts)
    for label in TZR_LABELS:
        if re.search(rf"\b{re.escape(label)}\b", haystack):
            return label
    return None


def tzr_detect_description(h1) -> Optional[str]:
    """First <p> after the h1 with meaningful length."""
    for p in h1.find_all_next("p", limit=15):
        text = p.get_text(" ", strip=True)
        if len(text) >= 40 and "godz." not in text.lower():
            return text
    return None


def parse_tzr_detail(url: str) -> Optional[Event]:
    soup = BeautifulSoup(http_get(url), "html.parser")

    h1 = soup.find("h1")
    if not h1:
        print(f"[warn] no <h1> at {url}", file=sys.stderr)
        return None
    # TZR glues a cycle label into the heading: <h1>Title<span class="info">dkf ekran</span></h1>
    for extra in h1.select("span.info"):
        extra.decompose()
    title = " ".join(h1.get_text(" ", strip=True).split())

    label = tzr_detect_label(soup, h1)
    description = tzr_detect_description(h1)

    # Collect all datetime mentions on the page and dedupe
    body_text = soup.get_text(" ", strip=True)
    matches = list(TZR_DATE_RX.finditer(body_text))
    if not matches:
        print(f"[warn] no dates at {url}", file=sys.stderr)
        return None
    dts = sorted({tzr_parse_dt(m) for m in matches})

    # Most TZR events happen in the theatre, but some are hosted elsewhere
    # (Fundacja Elektrowni, churches) — the title/description usually says so.
    venue = detect_venue(f"{title} {description or ''}", "Teatr Ziemi Rybnickiej")

    return Event(
        id="tzr-" + url.rstrip("/").split("/")[-1].removesuffix(".html"),
        title=title,
        category=classify(title, description, label, venue),
        start=iso(dts[0]),
        end=iso(dts[-1]) if len(dts) > 1 else None,
        venue=venue or "Teatr Ziemi Rybnickiej",
        description=description,
        sourceName="TZR",
        sourceUrl=url,
    )


def scrape_tzr() -> list[Event]:
    print(f"[info] TZR: fetching list {TZR_LIST_URL}", file=sys.stderr)
    urls = tzr_collect_urls(http_get(TZR_LIST_URL))
    print(f"[info] TZR: {len(urls)} event links", file=sys.stderr)

    events: list[Event] = []
    for i, url in enumerate(urls, 1):
        try:
            ev = parse_tzr_detail(url)
            if ev:
                events.append(ev)
        except Exception as e:  # noqa: BLE001 — one broken detail page is not fatal
            print(f"[error] TZR {url}: {e}", file=sys.stderr)
        if i % 10 == 0:
            print(f"[info] TZR: {i}/{len(urls)}", file=sys.stderr)
        time.sleep(0.3)  # be nice to the server
    return events


def fetch(params: dict, ctx: Ctx) -> list[Event]:
    return scrape_tzr()
