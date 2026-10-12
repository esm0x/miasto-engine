"""One site's articles as Google News indexes them, through its public RSS search.

Meant as a fallback (see "fallback" in modules/news.py), for a portal whose own feed
refuses CI: rybnik.com.pl sits behind a Cloudflare rule that answers 403 to datacentre
addresses, GitHub's runners included, while its robots.txt allows everything and the
same feed opens fine from a home connection. This does not get around that rule: it
does not touch the portal at all. It reads Google's index of it.

Params:
    {"name": "rybnik.com.pl",            # written into `source`, same as the primary
     "site": "rybnik.com.pl",
     "category": "Wiadomości",
     "skipTitles": "^(Portal informacyjny|Artykuły dla tagu)"}   # optional regex

Measured on 12 Oct 2026 against the portal's own feed: 100 items, 90 from the last
week, 34 of its 40 newest articles. What is lost: the lead (Google's description is
only the title again), so items carry no summary; and links go through
news.google.com, which redirects to the article when opened.

Google publishes these feeds without a key, but its terms speak of personal use; this
is a stopgap, the proper fix is the publisher allowing its own feed.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from urllib.parse import quote

from engine.common import UA, Ctx, get, log, strip_html
from modules.news import NewsItem, classify, item_id, parse_rfc822

# What Google indexes besides articles: the home page, tag pages, and the obituary
# section (death notices and funeral masses), which the portal's own feed leaves out.
DEFAULT_SKIP = (r"^(Portal informacyjny|Artykuły dla tagu|Artykuły z kategorii|Wiadomości z kategorii)"
                r"|^Z głębokim żalem|^Msza święta pogrzebowa|zawiadamiamy, że dnia")


def feed_url(site: str) -> str:
    return f"https://news.google.com/rss/search?q={quote('site:' + site)}&hl=pl&gl=PL&ceid=PL:pl"


def fetch(params: dict, ctx: Ctx, failures: list[dict]) -> list[NewsItem]:
    name = params["name"]
    skip = re.compile(params.get("skipTitles") or DEFAULT_SKIP, re.IGNORECASE)
    resp = get(feed_url(params["site"]), headers={"User-Agent": UA}, retries=2)
    root = ET.fromstring(resp.content)
    items: list[NewsItem] = []
    skipped = 0
    for node in root.findall(".//item"):
        raw_title = strip_html(node.findtext("title"))
        source = (node.findtext("source") or "").strip()
        # Google appends " - <publisher>" to every title.
        title = raw_title.rsplit(" - ", 1)[0].strip() if source and raw_title.endswith(source) else raw_title
        link = (node.findtext("link") or "").strip()
        published = parse_rfc822(node.findtext("pubDate"))
        if not title or not link or not published:
            continue
        if skip.search(title):
            skipped += 1
            continue
        items.append(NewsItem(
            id=item_id(link),
            title=title,
            summary="",
            link=link,
            published=published,
            source=name,
            category=params.get("category", "Wiadomości"),
            priority=classify(title, ""),
        ))
    log(f"[info] {name} via Google News: {len(items)} items ({skipped} listing pages skipped)")
    if not items:
        raise RuntimeError("Google News returned no articles")
    return items
