"""News and alerts → data/<slug>/news.json

    "news": {
      "maxItems": 120,              # optional
      "maxAgeDays": 365,            # NORMAL items older than this are dropped
      "extraAlertKeywords": [],     # stems added to ALERT_KEYWORDS for this city only
      "sources": [ {"type": "rss", "name": "Radio 90", "url": "...", "category": "Wiadomości", "cap": 40}, ... ]
    }

`priority` is the field that matters: ALERT (awarie, utrudnienia, ostrzeżenia) vs
NORMAL. ALERTs are never age-filtered, capped or dropped to make room. A `cap` on a
source limits its NORMAL items, so one prolific portal cannot crowd out the rest.

Output shape is fixed by scraper/CONTRACT.md (news.json) — Kotlin deserializes it 1:1,
so field names and the ALERT/NORMAL enum values are binding.
"""

from __future__ import annotations

import collections
import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import urlsplit, urlunsplit

from engine.common import UA, Ctx, fold, get, is_web_url, load_source, log, now_iso, write_json
from engine.contract import check_news

BROWSER_HEADERS = {
    "User-Agent": UA,
    "Accept": "application/rss+xml, application/xml;q=0.9, text/html;q=0.8, */*;q=0.7",
    "Accept-Language": "pl-PL,pl;q=0.9",
}

MAX_ITEMS = 120
SUMMARY_LEN = 300
POLITE_DELAY = 0.3
# NORMAL items older than this are dropped (turybnik.pl's feed still carries
# year-old SEO filler). ALERTs are never age-filtered.
MAX_AGE_DAYS = 365

# --------------------------------------------------------------------------
# ALERT detection — ONE list, tuned by hand. Matched against a diacritic-folded
# lowercase "title + summary", so stems are enough ("awari" catches awaria,
# awarii, awarie; "ostrzezeni" catches ostrzezenie/ostrzezenia).
# --------------------------------------------------------------------------
ALERT_KEYWORDS = [
    # Stems are cut before the inflected ending: "utrudnieni" caught "utrudnienia" but
    # not "utrudnień", so "Ogłoszenie w sprawie czasowych utrudnień w ruchu" went out
    # as an ordinary news item. Same for ostrzeżeń, zamknięć, skażeń.
    "utrudnien",
    "utrudnion",          # utrudniony / utrudniona / utrudnione przejazd, dojazd
    "ostrzezen",
    "brak wody",
    "brak pradu",
    "przerwa w dostaw",
    "wstrzymani dostaw",
    "wstrzymani ruchu",
    "wylaczeni",
    "wylaczen",
    "ewakuacj",
    "skazen",
    "nieprzejezdn",
    "ruch wahadlow",
    "niezdatn",           # woda niezdatna do picia / spożycia
    "gololedz",
]

# Words that only mean trouble in the right company. "objazd" alone flagged
# "Bosak rozpoczyna objazd po Polsce" — a campaign tour, not a detour — so it now
# needs a road word nearby. Add to this rather than to the list above when a keyword
# turns out to be ambiguous.
ROAD_CONTEXT = (
    # "drog" covers droga/drogi/drogowy; only ever checked next to a keyword above.
    "ruchu drogow", "organizacji ruchu", "ulic", "drodze", "drog",
    "kierowc", "skrzyzowani", "remont", "przejazd", "jezdni", "most", "wiadukt",
)
ALERT_KEYWORDS_IN_CONTEXT = {
    # Bare "ruch" is not usable as context — it matched "prezes Ruchu Narodowego".
    "objazd": ROAD_CONTEXT,
    # "zamknięta droga" is an alert, "za zamkniętymi drzwiami" is not.
    "zamkniet": ROAD_CONTEXT,
    # "zamknięcie drogi" yes, "planowane zamknięcie porodówki" (a political story) no.
    "zamkniec": ROAD_CONTEXT,
    "wylaczon": ("z ruchu", "pradu", "wody", "gazu", "ogrzewani"),
    # A service that is shut for the day: "PSZOK nieczynny 18-19 września".
    "nieczynn": ("pszok", "urzad", "punkt", "przychodni", "kasa", "biuro", "oczyszczalni"),
    "przekroczeni": ("norm", "parametr"),
    # Sanepid water notices: "niezgodność z wartością parametryczną", "brak
    # przydatności", "warunkowa przydatność" (drink only after boiling) are all an alert;
    # "stwierdza przydatność" is the all-clear and stays ordinary news.
    "niezgodnos": ("parametr", "wody"),
    "brak przydatnosci": ("wody", "spozyci"),
    "warunkow": ("przydatnos",),
    "zagrozeni": ("powodzi", "powodziow", "lawin"),
    # Bare "awari" made an ALERT of "Dlaczego kawa z ekspresu jest kwaśna" (Radio 90,
    # Żory, October 2026): a broken coffee machine is not a water main.
    "awari": ("wod", "prad", "ciepl", "gaz", "sieci", "kanaliz", "sygnaliz", "ogrzew", "energ",
              "kolej", "pociag", "autobus", "tramwaj", "drog", "ulic", "most", "trakcj", "linii",
              "zasilan", "oczyszczal", "pwik"),
    # Bare "alarm" caught "Sierpień 80 alarmował o cięciach" and a family training on
    # what sirens mean. A smog or flood alarm, or a siren test, still is one.
    "alarm": ("smog", "pyl", "powietrz", "powodz", "pogod", "imgw", "rcb", "burz", "wichur", "upal",
              "syren", "cwiczeni", "wykrywania"),
    # "wstrzymane dostawy ciepła" (PWiK Żory) slipped past "wstrzymani dostaw".
    "wstrzyman": ("dostaw", "ruchu", "ciepl", "kursow"),
}
# Deliberately NOT here: "smog" (matches eco advertorials) and the bare stem
# "zamkniet" (matches "zamknietych drzwiach" and similar prose).

PRIORITY_ALERT = "ALERT"
PRIORITY_NORMAL = "NORMAL"
# How long an ALERT from a keepPrevious source is carried over after it leaves the page.
KEPT_ALERT_DAYS = 14

EXTRA_KEYWORDS: list[str] = []


@dataclass
class NewsItem:
    id: str
    title: str
    summary: str
    link: str
    published: str      # ISO 8601 local, minute precision: YYYY-MM-DDTHH:MM
    source: str         # human-readable domain
    category: str
    priority: str       # ALERT | NORMAL


# --------------------------------------------------------------------------
# helpers shared by the sources
# --------------------------------------------------------------------------

def http_get(url: str):
    """GET with a short retry.

    rybnik.com.pl answers 403 to GitHub Actions runners while serving the same URL
    fine from a home connection, so the block is on the datacenter IP range, not on
    the User-Agent (verified: the bot UA gets 200 from a residential address).
    Retrying helps only when the refusal is rate-limiting rather than a hard block —
    when it is not, the caller records the failure and the other sources still run.
    """
    return get(url, headers=BROWSER_HEADERS, retries=2)


def item_id(link: str) -> str:
    return hashlib.sha1(link.encode("utf-8")).hexdigest()


def normalize_link(link: str) -> str:
    """Canonical form used for dedupe: drop query/fragment, trailing slash, scheme."""
    parts = urlsplit(link.strip())
    netloc = parts.netloc.lower().removeprefix("www.")
    path = parts.path.rstrip("/")
    return urlunsplit(("", netloc, path, "", ""))


def title_key(title: str) -> str:
    """Near-identical-title key: folded, alphanumerics only."""
    return re.sub(r"[^a-z0-9]+", "", fold(title))


def parse_rfc822(raw: Optional[str]) -> Optional[str]:
    """RFC-822 → ISO local naive 'YYYY-MM-DDTHH:MM'. None if unparseable."""
    if not raw or not raw.strip():
        return None
    try:
        dt = parsedate_to_datetime(raw.strip())
    except (TypeError, ValueError):
        return None
    if dt is None:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone().replace(tzinfo=None)
    return dt.isoformat(timespec="minutes")


def classify(title: str, summary: str, force_alert: bool = False) -> str:
    if force_alert:
        return PRIORITY_ALERT
    haystack = fold(f"{title} {summary}")
    for kw in [*ALERT_KEYWORDS, *EXTRA_KEYWORDS]:
        if kw in haystack:
            return PRIORITY_ALERT
    for kw, context in ALERT_KEYWORDS_IN_CONTEXT.items():
        if kw in haystack and any(c in haystack for c in context):
            return PRIORITY_ALERT
    return PRIORITY_NORMAL


# --------------------------------------------------------------------------
# merge
# --------------------------------------------------------------------------

def dedupe(items: Iterable[NewsItem]) -> list[NewsItem]:
    """First occurrence wins; ALERTs are processed first so they survive a clash."""
    ordered = sorted(items, key=lambda i: i.published, reverse=True)
    ordered.sort(key=lambda i: i.priority != PRIORITY_ALERT)  # stable: ALERTs first, newest first
    out: list[NewsItem] = []
    seen_links: set[str] = set()
    seen_titles: set[str] = set()
    for it in ordered:
        lkey, tkey = normalize_link(it.link), title_key(it.title)
        if lkey in seen_links or (tkey and tkey in seen_titles):
            continue
        seen_links.add(lkey)
        seen_titles.add(tkey)
        out.append(it)
    return out


def apply_caps(items: list[NewsItem], caps: dict[str, int], max_age_days: int) -> list[NewsItem]:
    """Per-source cap + age cut-off, on NORMAL items only — ALERTs are kept."""
    cutoff = (datetime.now() - timedelta(days=max_age_days)).isoformat(timespec="minutes")
    kept: list[NewsItem] = []
    used: dict[str, int] = {}
    for it in sorted(items, key=lambda i: i.published, reverse=True):
        if it.priority == PRIORITY_ALERT:
            kept.append(it)
            continue
        if it.published < cutoff:
            continue
        cap = caps.get(it.source)
        n = used.get(it.source, 0)
        if cap is not None and n >= cap:
            continue
        used[it.source] = n + 1
        kept.append(it)
    return kept


def enforce_total(items: list[NewsItem], limit: int = MAX_ITEMS) -> list[NewsItem]:
    """Cap the total, but NEVER drop an ALERT to make room for a NORMAL.

    The leftover room is filled round-robin across sources rather than by a flat
    date sort: turybnik.pl is stale by months and a flat sort wipes it out
    entirely, while rybnik.com.pl (300+ fresh items) would take every slot.
    """
    alerts = sorted([i for i in items if i.priority == PRIORITY_ALERT],
                    key=lambda i: i.published, reverse=True)
    room = max(0, limit - len(alerts))

    queues: dict[str, list[NewsItem]] = {}
    for it in sorted([i for i in items if i.priority != PRIORITY_ALERT],
                     key=lambda i: i.published, reverse=True):
        queues.setdefault(it.source, []).append(it)

    # Freshest source first, so it also wins the leftover slot in the last round.
    order = sorted(queues, key=lambda s: queues[s][0].published, reverse=True)
    picked: list[NewsItem] = []
    while len(picked) < room and any(queues[s] for s in order):
        for src in order:
            if len(picked) >= room:
                break
            if queues[src]:
                picked.append(queues[src].pop(0))

    merged = alerts + picked
    merged.sort(key=lambda i: i.published, reverse=True)
    return merged


def carry_over_failed(
    collected: list[NewsItem],
    failures: list[dict],
    out_path: Path,
    keep: frozenset[str] = frozenset(),
    max_age_days: int = MAX_AGE_DAYS,
) -> list[NewsItem]:
    """Reuse the previous run's items for any source that failed this time, and for the
    sources in `keep` always.

    rybnik.com.pl answers 403 to GitHub Actions runners while serving fine from a home
    connection, and it is the source of most ALERTs. Without this, every CI run replaced
    a good 120-item file with a 75-item one that had no current alerts at all — the app's
    home screen then had nothing to show. Keeping the last known items for a failed source
    means a blocked feed degrades slowly instead of wiping the section.

    `keep` is for a source that only ever shows its newest few: zory.pl lists nine
    items and has no second page, so without this a week of news would shrink to a
    day. Its items stay until maxAgeDays or maxItems push them out.
    """
    if not (failures or keep) or not out_path.exists():
        return []

    # Sections of one site are recorded as "rybnik.eu/dla-mieszkancow/..." while their
    # items carry plain "rybnik.eu", so compare on the part before the first slash —
    # otherwise the whole official-city section silently fails to be rescued.
    failed = {f["source"].split("/", 1)[0] for f in failures} | set(keep)
    try:
        previous = json.loads(out_path.read_text(encoding="utf-8")).get("items", [])
    except (OSError, json.JSONDecodeError) as e:
        log(f"[warn] cannot reuse previous news.json: {e}")
        return []

    have = {i.link for i in collected}
    revived: list[NewsItem] = []
    # A kept item lives only as long as its age allows, ALERTs included: they are never
    # aged out downstream, and a defaced page's fake "awaria" must not outlive its removal.
    now = datetime.now()
    keep_cutoff = (now - timedelta(days=max_age_days)).isoformat(timespec="minutes")
    alert_cutoff = (now - timedelta(days=KEPT_ALERT_DAYS)).isoformat(timespec="minutes")
    for raw in previous:
        if raw.get("source") in keep and raw.get("source") not in {f["source"].split("/", 1)[0] for f in failures}:
            published = str(raw.get("published", ""))
            if published < (alert_cutoff if raw.get("priority") == PRIORITY_ALERT else keep_cutoff):
                continue
        if raw.get("source") not in failed or raw.get("link") in have:
            continue
        try:
            revived.append(NewsItem(**raw))
        except TypeError:
            continue

    if revived:
        by_source = collections.Counter(i.source for i in revived)
        log(f"[warn] reusing previous items for failed sources: {dict(by_source)}")
    return revived


def report(items: list[NewsItem]) -> None:
    log("\n=== news.json verification ===")
    per_source: dict[str, int] = {}
    for it in items:
        per_source[it.source] = per_source.get(it.source, 0) + 1
    for src, n in sorted(per_source.items(), key=lambda kv: -kv[1]):
        log(f"[info] source {src:>16}: {n}")

    alerts = [i for i in items if i.priority == PRIORITY_ALERT]
    log(f"[info] priority ALERT={len(alerts)}  NORMAL={len(items) - len(alerts)}")
    if items:
        log(f"[info] newest published: {items[0].published}")
        log(f"[info] oldest published: {items[-1].published}")

    if not alerts:
        log("[warn] !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        log("[warn] ZERO ALERT ITEMS — the official source or the keyword")
        log("[warn] list may be broken. The point of this module is the alerts.")
        log("[warn] !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    else:
        log("[info] sample ALERT items:")
        for it in alerts[:3]:
            log(f"[info]   {it.published} [{it.source}/{it.category}] {it.title[:80]}")


# --------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------

def run(ctx: Ctx) -> dict:
    global EXTRA_KEYWORDS
    cfg = ctx.module("news") or {}
    EXTRA_KEYWORDS = [k.lower() for k in cfg.get("extraAlertKeywords", [])]
    out_path = ctx.data_dir / "news.json"

    collected: list[NewsItem] = []
    failures: list[dict] = []
    caps: dict[str, int] = {}

    for spec in cfg.get("sources", []):
        name = spec.get("name") or spec["type"]
        if spec.get("cap") is not None:
            caps[name] = int(spec["cap"])
        try:
            log(f"[info] fetching {name} ({spec['type']})")
            # A source may record partial failures itself (one section of a site),
            # and returns whatever it did get.
            collected.extend(load_source("news", spec["type"]).fetch(spec, ctx, failures))
        except Exception as e:  # noqa: BLE001 — one dead feed must not kill the run
            log(f"[error] {name}: {e}")
            failures.append({"source": name, "error": str(e)})
        time.sleep(POLITE_DELAY)

    keep = frozenset(spec.get("name") or spec["type"] for spec in cfg.get("sources", []) if spec.get("keepPrevious"))
    collected += carry_over_failed(collected, failures, out_path, keep, int(cfg.get("maxAgeDays", MAX_AGE_DAYS)))

    # A date in the future sorts first and never ages out; a day of clock skew is all a
    # real source needs.
    horizon = (datetime.now() + timedelta(days=1)).isoformat(timespec="minutes")
    future = [i for i in collected if i.published > horizon]
    for i in future:
        log(f"[warn] {i.source}: dropping item dated {i.published}: {i.title[:60]!r}")
    collected = [i for i in collected if i.published <= horizon]

    # A link that is not a web page (javascript:, intent:, file:) is a broken or hostile
    # source. Drop the item here so one bad entry cannot stop the whole file.
    bad = [i for i in collected if not is_web_url(i.link)]
    for i in bad:
        log(f"[warn] {i.source}: dropping item with non-web link {i.link[:60]!r}")
    collected = [i for i in collected if is_web_url(i.link)]

    items = enforce_total(
        apply_caps(dedupe(collected), caps, int(cfg.get("maxAgeDays", MAX_AGE_DAYS))),
        int(cfg.get("maxItems", MAX_ITEMS)),
    )
    report(items)

    payload = {
        "generated_at": now_iso(),
        "count": len(items),
        "failures": failures,
        "items": [asdict(i) for i in items],
    }
    check_news(payload)
    write_json(out_path, payload)
    log(f"[info] wrote {len(items)} items (failures: {len(failures)}) → {out_path}")
    return payload
