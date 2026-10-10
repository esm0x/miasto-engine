"""A list of notices on gov.pl, kept only where they name this gmina's places.

Every Powiatowa Stacja Sanitarno-Epidemiologiczna publishes on gov.pl in the same
layout, and its "Komunikaty i ostrzeżenia" carry what matters most to a household:
water from a given waterworks is unfit to drink, or fit only after boiling. A station
covers a whole powiat, so items are kept only when the title or the text names one of
`mentions`.

Params:
    {"name": "Sanepid Wodzisław", "url": "https://www.gov.pl/web/psse-wodzislaw-slaski/komunikaty",
     "mentions": ["Lubomi", "Syryni", "Bukow", "Buków", "Grabówk", "Nieboczow"],
     "maxDetails": 15,               # detail pages fetched per run, newest first
     "category": "Komunikaty"}

The list gives titles only, and every water notice is titled the same, so each detail
page is read for the place and for the date, which sits in the text as
"Komunikat nr 2 z dnia 12.07.2026".
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from engine.common import UA, Ctx, get, log, truncate
from modules.news import SUMMARY_LEN, NewsItem, classify, item_id
from sources import idcom

HEADERS = {"User-Agent": UA, "Accept-Language": "pl-PL,pl;q=0.9"}
DATED_RX = re.compile(r"z\s+dnia\s+(\d{1,2})[.\-](\d{1,2})[.\-](\d{4})", re.IGNORECASE)
ANY_DATE_RX = re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b")


def notice_date(text: str) -> Optional[datetime]:
    for rx in (DATED_RX, ANY_DATE_RX):
        m = rx.search(text)
        if m:
            try:
                return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            except ValueError:
                continue
    return None


def fetch(params: dict, ctx: Ctx, failures: list[dict]) -> list[NewsItem]:
    name = params["name"]
    mentions = re.compile("|".join(re.escape(m) for m in params["mentions"]), re.IGNORECASE)
    page = BeautifulSoup(get(params["url"], headers=HEADERS, retries=2).text, "html.parser")
    area = page.select_one("article.article-area__article") or page
    links: list[str] = []
    for a in area.select(".art-prev .title a[href], .art-prev li a[href]"):
        url = urljoin(params["url"], a["href"])
        if url not in links and "/web/" in url:
            links.append(url)
    log(f"[info] {name}: {len(links)} komunikatów na liście")

    items: list[NewsItem] = []
    for url in links[: int(params.get("maxDetails", 15))]:
        try:
            detail = BeautifulSoup(get(url, headers=HEADERS, retries=1).text, "html.parser")
        except Exception as e:  # noqa: BLE001
            log(f"[warn] {name} {url}: {e}")
            continue
        art = detail.select_one("article.article-area__article") or detail.select_one("article")
        if not art:
            continue
        text = " ".join(art.get_text(" ", strip=True).split())
        heading = art.find(["h1", "h2"])
        title = " ".join(heading.get_text(" ", strip=True).split()) if heading else ""
        if not title or not mentions.search(f"{title} {text} {url}"):
            idcom.polite()
            continue
        published = notice_date(text)
        if not published:
            log(f"[warn] {name}: no date in {url}")
            idcom.polite()
            continue
        body = text[len(title):].strip() if text.startswith(title) else text
        summary = truncate(body.split(" Materiały ")[0], SUMMARY_LEN)
        items.append(NewsItem(
            id=item_id(url),
            title=title,
            summary=summary,
            link=url,
            published=published.isoformat(timespec="minutes"),
            source=name,
            category=params.get("category", "Komunikaty"),
            priority=classify(title, summary),
        ))
        idcom.polite()
    log(f"[info] {name}: {len(items)} dotyczy tej gminy")
    return items
