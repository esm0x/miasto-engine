"""Any RSS 2.0 feed.

Params:
    {"name": "Radio 90",                  # written into `source`
     "url": "https://www.radio90.pl/tag/rybnik/feed",
     "category": "Wiadomości",            # default category
     "useFeedCategory": false,            # take <category> from the feed when present
     "cap": 40,                           # NORMAL items kept from this source (module-level)
     "maxAgeDays": 365}                   # optional: drop older items, alerts included

Regional portals are the cheap win for a new town: Radio 90 has a tag feed per town,
nowiny.pl and the tu<miasto>.pl network cover several at once.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Optional

from engine.common import Ctx, log, strip_html, truncate
from modules.news import SUMMARY_LEN, NewsItem, classify, http_get, item_id, parse_rfc822


def rss_text(item: ET.Element, tag: str) -> Optional[str]:
    el = item.find(tag)
    return el.text if el is not None and el.text else None


def fetch(params: dict, ctx: Ctx, failures: list[dict]) -> list[NewsItem]:
    source = params["name"]
    log(f"[info] fetching RSS {params['url']}")
    resp = http_get(params["url"])
    root = ET.fromstring(resp.content)  # bytes → lets ET honour the XML decl
    items: list[NewsItem] = []
    skipped_dates = 0
    # A tag feed is an archive: Radio 90's "grabowka" reaches back to 2012. The module
    # never ages out alerts (an official notice stays until it is gone), so a source
    # that is really an archive cuts its own tail.
    cutoff = None
    if params.get("maxAgeDays"):
        cutoff = (datetime.now() - timedelta(days=int(params["maxAgeDays"]))).isoformat(timespec="minutes")

    for node in root.findall(".//item"):
        link = (rss_text(node, "link") or rss_text(node, "guid") or "").strip()
        title = strip_html(rss_text(node, "title"))
        if not link or not title:
            continue

        published = parse_rfc822(rss_text(node, "pubDate"))
        if not published:
            # Never invent now() — an item with a bogus date would jump the list.
            skipped_dates += 1
            continue
        if cutoff and published < cutoff:
            continue

        summary = truncate(strip_html(rss_text(node, "description")), SUMMARY_LEN)
        category = params.get("category", "Wiadomości")
        if params.get("useFeedCategory"):
            feed_cat = strip_html(rss_text(node, "category"))
            if feed_cat:
                category = feed_cat

        items.append(NewsItem(
            id=item_id(link),
            title=title,
            summary=summary,
            link=link,
            published=published,
            source=source,
            category=category,
            priority=classify(title, summary),
        ))

    if skipped_dates:
        log(f"[warn] {source}: skipped {skipped_dates} item(s) with unparseable pubDate")
    log(f"[info] {source}: parsed {len(items)} items")
    return items
