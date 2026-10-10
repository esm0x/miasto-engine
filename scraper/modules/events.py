"""Events → data/<slug>/events.json

Each source in sources.json["events"]["sources"] is a parser in sources/events/, called
in order; a source that raises is recorded in `failures` and never aborts the run.
Everything is merged here, filtered to the future, deduplicated on (normalised title,
start date) and written as one payload.

What is shared lives here, so every source agrees: the category rules, the venue
detection and the dedupe. What is local, the venue names of this town and the words
that are its own name, comes from the module's settings:

    "events": {
      "venues": [["regex", "Canonical venue name"], ...],
      "clubVenues": "regex of venues whose unclassified events are nightlife",
      "cityWords": ["rybnik", "rybniku", ...],   # ignored when comparing titles
      "sourceRank": {"TZR": 0, ...},             # lower wins a tie on description length
      "extraCategoryRules": [["Festiwal", "kiermasz|festyn"], ...],  # tried after the shared rules
      "sources": [ {"type": "tzr", "name": "TZR"}, ... ]
    }

Category strings MUST match Android's EventCategory enum names (see CONTRACT.md).
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Iterable, Optional

from bs4 import BeautifulSoup

from engine.common import Ctx, clean_text, get, is_web_url, load_source, log, now_iso, strip_accents, write_json
from engine.contract import check_events

TIMEOUT = 30

VALID_CATEGORIES = {
    "Koncert", "Spektakl", "Kabaret", "Film", "Festiwal", "Wystawa",
    "Warsztaty", "Impreza", "Sport", "DlaDzieci", "Inne",
}


@dataclass
class Event:
    id: str
    title: str
    category: str
    start: str        # ISO 8601 local time (Europe/Warsaw implied)
    end: Optional[str]
    venue: str
    description: Optional[str]
    sourceName: str
    sourceUrl: str


# --------------------------------------------------------------------------- #
# per-run settings, set by configure() from the city's sources.json
# --------------------------------------------------------------------------- #

CITY_NAME = ""
VENUE_PATTERNS: list[tuple[str, str]] = []
CLUB_VENUES = r"(?!)"          # matches nothing until a city says otherwise
SOURCE_RANK: dict[str, int] = {}
CITY_WORDS: set[str] = set()
EXTRA_RULES: list[tuple[str, str]] = []


def configure(ctx: Ctx, cfg: dict) -> None:
    global CITY_NAME, VENUE_PATTERNS, CLUB_VENUES, SOURCE_RANK, CITY_WORDS, EXTRA_RULES
    CITY_NAME = ctx.name
    VENUE_PATTERNS = [(p, n) for p, n in cfg.get("venues", [])]
    CLUB_VENUES = cfg.get("clubVenues") or r"(?!)"
    SOURCE_RANK = dict(cfg.get("sourceRank", {}))
    CITY_WORDS = {w.lower() for w in cfg.get("cityWords", [])}
    EXTRA_RULES = [(c, p) for c, p in cfg.get("extraCategoryRules", [])]
    bad = [c for c, _ in EXTRA_RULES if c not in VALID_CATEGORIES]
    if bad:
        raise ValueError(f"extraCategoryRules: unknown categories {bad}")


# --------------------------------------------------------------------------- #
# HTTP / text helpers
# --------------------------------------------------------------------------- #

def http_get(url: str, session=None) -> str:
    return get(url, session=session, timeout=TIMEOUT, fix_latin1=True).text


def get_soup(url: str, session=None) -> BeautifulSoup:
    return BeautifulSoup(http_get(url, session), "html.parser")


def normalise_title(title: str) -> str:
    """Lowercase, drop accents and punctuation, collapse whitespace — dedup key."""
    s = strip_accents(title).lower()
    s = re.sub(r"[^\w\s]+", " ", s, flags=re.UNICODE)
    return " ".join(s.split())


def slugify(s: str, max_len: int = 60) -> str:
    s = strip_accents(s).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:max_len].strip("-") or "event"


def iso(dt: datetime) -> str:
    return dt.replace(second=0, microsecond=0).isoformat(timespec="minutes")


def parse_iso_local(value: str) -> datetime:
    """'2026-10-16T18:00:00+02:00' → naive local datetime (offsets here are already
    Europe/Warsaw, so dropping the tzinfo keeps the correct wall-clock time)."""
    dt = datetime.fromisoformat(value.strip())
    return dt.replace(tzinfo=None)


# --------------------------------------------------------------------------- #
# Shared classification — one place, so every source agrees
# --------------------------------------------------------------------------- #

# Ordered: first rule whose pattern matches wins.
# A title that says "for kids" outright wins over everything else: a Halloween
# party for toddlers belongs in DlaDzieci, not Impreza. Deliberately checked on
# the *title* only — source labels and descriptions mention children far too
# loosely ("zapraszamy dzieci") to be trusted with this.
KIDS_TITLE_RX = (r"dla dzieci|dla najmlodsz|dla najmłodsz|dla maluch|dla przedszkolak|"
                 r"najnaj|\bkids\b|\bbaby\b|dzieciom|dla rodzin|familijn|dla calej rodziny|"
                 r"dla całej rodziny")

CATEGORY_RULES: list[tuple[str, str]] = [
    ("Impreza", r"\bimprez|potancowk|potańcówk|potancowk|dyskotek|\bdj\b|dj set|dj-set|"
                r"techno|house music|\brave\b|silent\s?disco|\bdisco\b|after\s?party|\bparty\b|\bnight\b|"
                r"parkiet|zabawa taneczna|sylwester|andrzejk|halloween|juwenalia|"
                r"klubow|do bialego rana|do białego rana|\bbal\b|sub-?club"),
    ("Sport", r"zuzl|zuzel|żużl|żużel|speedway|row rybnik|ekstraliga|\bliga\b|\bmecz\b|"
              r"turniej|\bbieg\b|biegow|maraton|\bmtb\b|rowerow|zawody|wyscig|wyścig|"
              r"crossfit|\bfit\b|fitness|games rx|paintball|wspinacz|\brace\b|extreme|"
              r"\brajd\b|sparing|puchar\b"),
    ("Kabaret", r"kabaret|stand-?\s?up|standup"),
    ("Koncert", r"\bkoncert|recital|unplugged|akustyczn|live music|jam session|"
                r"przeglad kapel|przegląd kapel|\btour\b|zagraj[aą]|\bgig\b|piosenk"),
    ("Film", r"\bfilm|\bkino\b|seans|projekcja|\bdkf\b|screening|kinow"),
    ("Wystawa", r"wystaw|wernisa|galeri|ekspozycj|malarstw"),
    ("Warsztaty", r"warsztat|zaj[eę]cia|\bkurs\b|szkolen|lekcj|master ?class|"
                  r"spotkanie autorskie|prelekcj|\bwyklad|\bwykład"),
    ("Spektakl", r"spektakl|teatr|musical|operetk|\bopera\b|\bbalet|monodram|"
                 r"przedstawien|widowisk|komedia"),
    ("Festiwal", r"festiwal|festival|jarmark|\bfest\b|przegl[aą]d"),
    ("DlaDzieci", r"dzieci|najmlodsz|najmłodsz|bajk|familijn|rodzinn|maluch|"
                  r"przedszkol|teatrzyk|\bferie\b|poranek"),
]


def _first_match(haystack: str) -> Optional[str]:
    # A city's own rules come after the shared ones: they fill gaps ("kiermasz" in a
    # village) without overriding what every city agrees on (an andrzejki party is
    # Impreza even when the portal files it under "Festyny, pikniki").
    for category, pattern in [*CATEGORY_RULES, *EXTRA_RULES]:
        if re.search(pattern, haystack, re.IGNORECASE):
            return category
    return None


def classify(
    title: str,
    description: Optional[str] = None,
    source_hint: Optional[str] = None,
    venue: Optional[str] = None,
) -> str:
    """Map a free-text event onto the EventCategory enum.

    Two passes: the title (plus whatever label the source gave us) is trusted
    first, the long description only as a fallback — descriptions are noisy and
    a concert blurb mentioning "dzieci" should not become DlaDzieci.
    """
    if re.search(KIDS_TITLE_RX, strip_accents(title).lower() + " " + title.lower(), re.IGNORECASE):
        return "DlaDzieci"

    primary = " ".join(x for x in (title, source_hint) if x)
    category = _first_match(strip_accents(primary).lower() + " " + primary.lower())
    if not category and description:
        category = _first_match(strip_accents(description).lower() + " " + description.lower())
    if not category:
        category = "Inne"
    if category == "Inne" and venue and re.search(CLUB_VENUES, venue, re.IGNORECASE):
        category = "Impreza"
    return category


# --------------------------------------------------------------------------- #
# Shared venue detection
# --------------------------------------------------------------------------- #

CHURCH_RX = re.compile(
    r"kości[oe]?[łl]\w*\s+(?:pw\.\s*)?((?:św\.|Św\.)\s*[\wąćęłńóśźż]+(?:\s+[\wąćęłńóśźż]+)?)",
    re.IGNORECASE,
)


def detect_venue(text: str, default: Optional[str] = None) -> Optional[str]:
    """Pull a real venue name out of a title/description blob."""
    if not text:
        return default
    for pattern, name in VENUE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return name
    m = CHURCH_RX.search(text)
    if m:
        return "Kościół " + " ".join(m.group(1).split())
    return default


# --------------------------------------------------------------------------- #
# Merge / dedupe
# --------------------------------------------------------------------------- #

def _richness(ev: Event) -> tuple[int, int]:
    """Higher is better: longer description first, then source preference."""
    return (len(ev.description or ""), -SOURCE_RANK.get(ev.sourceName, 2))


def _merge_venue(keep: Event, drop: Event) -> None:
    generic = ("", CITY_NAME.lower())
    if keep.venue.strip().lower() in generic and drop.venue.strip().lower() not in generic:
        keep.venue = drop.venue
    if keep.end is None and drop.end is not None:
        keep.end = drop.end


# Words that carry no identity — ignored when comparing two titles. The city's own
# name in its inflected forms is added from the config.
TITLE_STOPWORDS = {
    "w", "we", "z", "za", "i", "na", "do", "o", "od", "po", "przy", "oraz", "a",
    "the", "czyli", "vol", "dla",
    "koncert", "koncerty", "spektakl", "wydarzenie", "bilety",
}


def significant_tokens(title: str) -> set[str]:
    stop = TITLE_STOPWORDS | CITY_WORDS
    return {t for t in normalise_title(title).split() if len(t) > 2 and t not in stop}


def deduplicate(events: list[Event]) -> tuple[list[Event], int]:
    """Key: (normalised title, start date). Two further passes fold in the same
    event announced under a decorated title ("Rybnik: Niezły Burdel – komedia
    teatralna" vs "Niezły burdel") — by whole-phrase containment on the same day,
    and by shared distinctive words at the exact same start time."""
    by_key: dict[tuple[str, str], Event] = {}
    dropped = 0
    for ev in sorted(events, key=_richness, reverse=True):
        key = (normalise_title(ev.title), ev.start[:10])
        if key in by_key:
            _merge_venue(by_key[key], ev)
            dropped += 1
        else:
            by_key[key] = ev

    kept: list[Event] = []
    per_day: dict[str, list[Event]] = {}
    for ev in sorted(by_key.values(), key=_richness, reverse=True):
        norm = normalise_title(ev.title)
        same_day = per_day.setdefault(ev.start[:10], [])
        duplicate = None
        for other in same_day:
            a, b = norm, normalise_title(other.title)
            short, long = (a, b) if len(a) <= len(b) else (b, a)
            if len(short) >= 12 and len(short.split()) >= 2 and re.search(
                rf"(?:^|\s){re.escape(short)}(?:\s|$)", long
            ):
                duplicate = other
                break
        if duplicate is not None:
            _merge_venue(duplicate, ev)
            dropped += 1
            continue
        same_day.append(ev)
        kept.append(ev)

    # Third pass: identical start *time* + two or more distinctive words in
    # common. Same-slot collisions between genuinely different events are rare,
    # while the same gig listed by three portals is the norm here.
    final: list[Event] = []
    per_slot: dict[str, list[tuple[Event, set[str]]]] = {}
    for ev in kept:
        tokens = significant_tokens(ev.title)
        slot = per_slot.setdefault(ev.start, [])
        twin = next((other for other, other_tokens in slot if len(tokens & other_tokens) >= 2), None)
        if twin is not None:
            _merge_venue(twin, ev)
            dropped += 1
            continue
        slot.append((ev, tokens))
        final.append(ev)
    return final, dropped


def ensure_unique_ids(events: Iterable[Event]) -> None:
    seen: set[str] = set()
    for ev in events:
        base = ev.id
        n = 2
        while ev.id in seen:
            ev.id = f"{base}-{n}"
            n += 1
        seen.add(ev.id)


# --------------------------------------------------------------------------- #
# run
# --------------------------------------------------------------------------- #

def run(ctx: Ctx) -> dict:
    cfg = ctx.module("events") or {}
    configure(ctx, cfg)

    all_events: list[Event] = []
    failures: list[dict] = []
    per_source_raw: dict[str, int] = {}

    for spec in cfg.get("sources", []):
        name = spec.get("name") or spec["type"]
        log(f"\n[info] === {name} ===")
        try:
            events = load_source("events", spec["type"]).fetch(spec, ctx)
        except Exception as e:  # noqa: BLE001 — one dead site must not kill the run
            log(f"[error] source {name} failed: {e}")
            failures.append({"source": name, "error": f"{type(e).__name__}: {e}"})
            per_source_raw[name] = 0
            continue
        per_source_raw[name] = len(events)
        all_events.extend(events)

    # The app only opens http(s); anything else becomes "no link" rather than a reason
    # to reject the whole file.
    for e in all_events:
        if e.sourceUrl and not is_web_url(e.sourceUrl):
            log(f"[warn] {e.sourceName}: dropping non-web link {e.sourceUrl[:60]!r}")
            e.sourceUrl = ""

    # Keep future/current only (grace: 3h after start for last-minute checkers)
    cutoff = iso(datetime.now() - timedelta(hours=3))
    future = [e for e in all_events if (e.end or e.start) >= cutoff]
    events, dropped = deduplicate(future)
    events.sort(key=lambda e: (e.start, e.title))
    ensure_unique_ids(events)

    payload = {
        "generated_at": now_iso(),
        "sources": sorted({e.sourceName for e in events}),
        "count": len(events),
        "failures": failures,
        "events": [asdict(e) for e in events],
    }
    report(per_source_raw, future, events, dropped)
    check_events(payload)
    write_json(ctx.data_dir / "events.json", payload)
    log(f"\n[info] wrote {len(events)} events (failures: {len(failures)}) → {ctx.data_dir / 'events.json'}")
    return payload


def report(per_source_raw, future, events, dropped) -> None:
    log("\n" + "=" * 62)
    log("PER-SOURCE COUNTS (scraped → upcoming → kept after dedup)")
    kept_by_source = Counter(e.sourceName for e in events)
    upcoming_by_source = Counter(e.sourceName for e in future)
    for name, raw in per_source_raw.items():
        log(f"  {name:<16} {raw:>4} → {upcoming_by_source.get(name, 0):>4} → "
            f"{kept_by_source.get(name, 0):>4}")
    log(f"  {'TOTAL':<16} {sum(per_source_raw.values()):>4} → {len(future):>4} → "
        f"{len(events):>4}   (deduped away: {dropped})")

    log("\nCATEGORY HISTOGRAM")
    hist = Counter(e.category for e in events)
    for cat, n in hist.most_common():
        log(f"  {cat:<12} {n:>4}  {'#' * n}")

    log("\nSAMPLES (one per source)")
    shown: set[str] = set()
    for e in events:
        if e.sourceName in shown:
            continue
        shown.add(e.sourceName)
        log(f"  [{e.sourceName}] {e.start} | {e.category:<9} | {e.title[:52]}\n"
            f"      @ {e.venue[:70]}")
