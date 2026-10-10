"""News from an IDcom municipal portal (see sources/idcom.py).

Params:
    {"name": "lubomia.pl", "base": "https://lubomia.pl",
     "categories": [{"id": 1, "name": "Aktualności", "pages": 1},
                    {"id": 4, "name": "Ogłoszenia", "pages": 1, "forceAlert": false}]}

Each list page holds about 16 tiles. Tiles carry neither the full title nor a date, so
every item costs one detail request; keep `pages` small.
"""

from __future__ import annotations

from typing import Optional

from engine.common import Ctx, log, truncate
from modules.news import SUMMARY_LEN, NewsItem, classify, item_id
from sources import idcom


def list_url(base: str, category: dict, page: int) -> str:
    if page == 1:
        return f"{base}/wiadomosci/kategoria/{category['id']}"
    return f"{base}/wiadomosci/kategoria/{category['id']}/strona/{page}/x"


def parse_detail(url: str, name: str, category: dict) -> Optional[NewsItem]:
    page = idcom.soup(url)
    title = idcom.meta(page, "og:title")
    when_el = page.select_one(".article__metatags_when")
    published = idcom.parse_date(when_el.get_text(" ", strip=True)) if when_el else None
    if not title or not published:
        log(f"[warn] {name}: no title or date at {url}")
        return None
    lead = idcom.meta(page, "og:description") or idcom.meta(page, "description") or ""
    summary = truncate(" ".join(lead.split()), SUMMARY_LEN)
    # The page's own category element repeats its label ("Aktualności Aktualności"),
    # and the list we came from already says which category this is.
    label = category["name"]
    return NewsItem(
        id=item_id(url),
        title=title,
        summary=summary,
        link=url,
        published=published.isoformat(timespec="minutes"),
        source=name,
        category=label,
        priority=classify(title, summary, force_alert=bool(category.get("forceAlert"))),
    )


def fetch(params: dict, ctx: Ctx, failures: list[dict]) -> list[NewsItem]:
    name = params.get("name") or params["base"].split("//", 1)[-1]
    base = params["base"].rstrip("/")
    items: list[NewsItem] = []
    seen: set[str] = set()
    for category in params["categories"]:
        try:
            for page in range(1, int(category.get("pages", 1)) + 1):
                links = idcom.detail_links(idcom.soup(list_url(base, category, page)), base, "wiadomosci")
                log(f"[info] {name} {category['name']} p.{page}: {len(links)} wpisów")
                for url in links:
                    if url in seen:
                        continue
                    seen.add(url)
                    try:
                        item = parse_detail(url, name, category)
                        if item:
                            items.append(item)
                    except Exception as e:  # noqa: BLE001 — one broken page is not fatal
                        log(f"[warn] {name} {url}: {e}")
                    idcom.polite()
        except Exception as e:  # noqa: BLE001
            log(f"[error] {name} {category['name']}: {e}")
            failures.append({"source": f"{name}/{category['name']}", "error": str(e)})
    return items
