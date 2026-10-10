"""A news list of tiles: <article> with a <time>DD.MM.YYYY</time> and an <h3><a> title.

A pattern of small Polish CMSes; first used for GOKSiR Lubomia (goksirlubomia.pl, CMS
by wrobelek.eu), whose homepage pages through ?page5122=0,5,10… five tiles at a time.

Params:
    {"name": "GOKSiR Lubomia", "base": "https://goksirlubomia.pl/",
     "linkPattern": "aktualnosci-szczegoly/",   # only tiles linking here count
     "pageParam": "page5122", "pageSize": 5, "pages": 4,
     "category": "Kultura",
     "skipTitles": "^Grafik tygodniowy$"}       # optional regex, case-insensitive

The tile's date is the publication date, which is what news needs. The detail page is
fetched only for a lead (og:description); many posts are a poster image and nothing
else, and then the summary stays empty rather than repeating the title.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from engine.common import UA, Ctx, clean_text, get, log, same_site, truncate
from modules.news import SUMMARY_LEN, NewsItem, classify, item_id
from sources import idcom

HEADERS = {"User-Agent": UA, "Accept-Language": "pl-PL,pl;q=0.9"}
DATE_RX = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})")


def tiles(html: str, base: str, link_pattern: str) -> list[tuple[str, str, datetime]]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[tuple[str, str, datetime]] = []
    for art in soup.select("article"):
        link = art.select_one(f'h3 a[href*="{link_pattern}"]') or art.select_one(f'a[href*="{link_pattern}"][title]')
        time_el = art.find("time")
        if not link or not time_el:
            continue
        m = DATE_RX.search(time_el.get_text(strip=True))
        title = clean_text(link.get("title") or link.get_text(" ", strip=True))
        if not m or not title:
            continue
        try:
            published = datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            continue
        url = urljoin(base, link["href"])
        if not same_site(url, urlsplit(base).hostname or ""):
            continue  # a tile pointing off-site is not this site's news
        out.append((url, title, published))
    return out


def lead(url: str) -> str:
    try:
        page = BeautifulSoup(get(url, headers=HEADERS, retries=1).text, "html.parser")
    except Exception:  # noqa: BLE001 — a missing lead is not worth losing the item
        return ""
    text = idcom.meta(page, "og:description") or idcom.meta(page, "description") or ""
    # A lead that is only a file path or a form label says nothing to a reader.
    if "/assets/" in text or len(text) < 25:
        return ""
    return truncate(" ".join(text.split()), SUMMARY_LEN)


def fetch(params: dict, ctx: Ctx, failures: list[dict]) -> list[NewsItem]:
    name = params["name"]
    base = params["base"]
    skip = re.compile(params["skipTitles"], re.IGNORECASE) if params.get("skipTitles") else None
    seen: set[str] = set()
    items: list[NewsItem] = []
    for page in range(int(params.get("pages", 1))):
        url = base
        if page and params.get("pageParam"):
            sep = "&" if "?" in base else "?"
            url = f"{base}{sep}{params['pageParam']}={page * int(params.get('pageSize', 5))}"
        found = tiles(get(url, headers=HEADERS, retries=2).text, base, params["linkPattern"])
        log(f"[info] {name} p.{page + 1}: {len(found)} wpisów")
        for link, title, published in found:
            if link in seen or (skip and skip.search(title)):
                continue
            seen.add(link)
            summary = lead(link)
            idcom.polite()
            items.append(NewsItem(
                id=item_id(link),
                title=title,
                summary=summary,
                link=link,
                published=published.isoformat(timespec="minutes"),
                source=name,
                category=params.get("category", "Wiadomości"),
                priority=classify(title, summary),
            ))
        if not found:
            break

    # A post with no text of its own gets the site's default description ("Lubomia jest
    # położona bardzo atrakcyjnie…"). Any lead shared by two posts is that boilerplate.
    leads = [i.summary for i in items if i.summary]
    boiler = {s for s in leads if leads.count(s) > 1}
    for i in items:
        if i.summary in boiler:
            i.summary = ""
            i.priority = classify(i.title, "")
    return items
