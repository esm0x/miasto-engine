"""rybnik.eu: TYPO3 news lists, scraped directly because the site has NO feed at all
(every feed path 404s). This is the official city source and carries the
outage/disruption notices, which are the whole point of the module.

Params:
    {"name": "rybnik.eu", "base": "https://www.rybnik.eu",
     "sections": [{"path": "/dla-mieszkancow/aktualnosci", "category": "Aktualności",
                   "forceAlert": false, "pages": 2}, ...]}

A failing section is recorded as "<name><path>" and the rest still run; news.py's
carry-over matches it back to the items by the part before the first slash.

Another TYPO3 site lays its list out differently; zory.pl has no <article>, each item is
one link. Optional params say where things are:
    "item": "a.newsitem", "title": "span.newsitemtxt"
The item is the link itself when it is an <a>; date and category are read the same way.
"""

from __future__ import annotations

import re
import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from engine.common import Ctx, log, strip_html, truncate
from modules.news import POLITE_DELAY, SUMMARY_LEN, NewsItem, classify, http_get, item_id


def eu_teaser(url: str, cache: dict[str, str]) -> str:
    """The list view carries no teaser, so pull the detail page's meta description."""
    if url in cache:
        return cache[url]
    teaser = ""
    try:
        soup = BeautifulSoup(http_get(url).text, "html.parser")
        meta = (soup.select_one('meta[name="description"]')
                or soup.select_one('meta[property="og:description"]'))
        if meta and meta.get("content"):
            teaser = strip_html(meta["content"])
        if not teaser:
            for p in soup.select("p"):
                text = p.get_text(" ", strip=True)
                if len(text) >= 60:
                    teaser = " ".join(text.split())
                    break
    except Exception as e:  # noqa: BLE001 — a missing teaser must not kill the item
        log(f"[warn] teaser failed {url}: {e}")
    teaser = truncate(teaser, SUMMARY_LEN)
    cache[url] = teaser
    time.sleep(POLITE_DELAY)
    return teaser


def parse_section(base: str, name: str, section: dict, teaser_cache: dict[str, str]) -> list[NewsItem]:
    items: list[NewsItem] = []
    seen: set[str] = set()

    for page in range(1, int(section.get("pages", 1)) + 1):
        path = section["path"] if page == 1 else f"{section['path']}/page-{page}"
        url = urljoin(base, path)
        soup = BeautifulSoup(http_get(url).text, "html.parser")
        articles = soup.select(section.get("item") or "article")
        log(f"[info] {name} {path}: {len(articles)} articles")

        for art in articles:
            if section.get("item"):
                anchor = art if art.name == "a" and art.get("href") else art.find("a", href=True)
                title_el = art.select_one(section["title"]) if section.get("title") else anchor
            else:
                heading = art.find(["h2", "h3"])
                anchor = title_el = heading.find("a", href=True) if heading else None
            if not anchor or not title_el:
                continue
            link = urljoin(base, anchor["href"])
            title = " ".join(title_el.get_text(" ", strip=True).split())
            if not title or link in seen:
                continue

            time_el = art.find("time")
            raw_date = (time_el.get("datetime") if time_el else None) or ""
            date_match = re.match(r"(\d{4})-(\d{2})-(\d{2})", raw_date.strip())
            if not date_match:
                log(f"[warn] {name}: no usable date for {link}")
                continue
            # TYPO3 gives date only; 00:00 keeps the ISO shape the contract wants.
            published = f"{date_match.group(0)}T00:00"

            cat_el = art.select_one("span.category")
            category = (cat_el.get_text(" ", strip=True) if cat_el else "") or section["category"]

            summary = eu_teaser(link, teaser_cache)
            seen.add(link)
            items.append(NewsItem(
                id=item_id(link),
                title=title,
                summary=summary,
                link=link,
                published=published,
                source=name,
                category=category,
                priority=classify(title, summary, force_alert=bool(section.get("forceAlert"))),
            ))
        time.sleep(POLITE_DELAY)

    return items


def fetch(params: dict, ctx: Ctx, failures: list[dict]) -> list[NewsItem]:
    name = params.get("name", "rybnik.eu")
    base = params["base"]
    teaser_cache: dict[str, str] = {}
    collected: list[NewsItem] = []
    for section in params["sections"]:
        try:
            log(f"[info] scraping {name} {section['path']}")
            collected.extend(parse_section(base, name, section, teaser_cache))
        except Exception as e:  # noqa: BLE001
            log(f"[error] {name} {section['path']}: {e}")
            failures.append({"source": f"{name}{section['path']}", "error": str(e)})
    return collected
