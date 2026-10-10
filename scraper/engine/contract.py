"""Contract checks, run on every payload before it is written.

scraper/CONTRACT.md is binding: Kotlin deserialises these files 1:1, and an enum value
it does not know or a malformed date costs the user data, sometimes a crash. With one
city that was caught by eye; with ten it has to be caught by the build. A violation
raises ContractError, the module writes nothing, and the previous good file stays
published. Better stale data than data the app cannot read.

Deliberately structural: these checks do not judge whether the data is plausible (that
is each module's report), only whether the app can read it.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Iterable

EVENT_CATEGORIES = {
    "Koncert", "Spektakl", "Kabaret", "Film", "Festiwal", "Wystawa",
    "Warsztaty", "Impreza", "Sport", "DlaDzieci", "Inne",
}
WASTE_TYPES = {"ZMIESZANE", "POPIOLY", "SEGREGOWANE", "BIO", "GABARYTY", "PLASTIK", "PAPIER", "SZKLO"}
HOUSE_TYPES = {"SINGLE_FAMILY", "MULTI_FAMILY"}
PARITIES = {"ODD", "EVEN", None}
WEEKDAYS = {"MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"}
PRIORITIES = {"ALERT", "NORMAL"}
SPORTS = {"FOOTBALL", "FOOTBALL_W", "SPEEDWAY"}
MATCH_STATUSES = {"SCHEDULED", "FINISHED"}
STAGES = {"REGULAR", "PLAYOFF", "PLAYDOWN", "BARRAGE", "CUP"}
POINT_KINDS = {"PSZOK", "GPZON"}
GUIDE_WHERE = {"ZMIESZANE", "BIO", "PAPIER", "SZKLO", "PLASTIK", "POPIOLY", "GABARYTY", "PSZOK", "GPZON"}

MINUTE_RX = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$")
DAY_RX = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HHMM_RX = re.compile(r"^\d{2}:\d{2}$")


# Generous ceilings, an order of magnitude above anything real (Rybnik: ~130 events,
# 120 news, 98 rejony). Past them a source has gone wrong, not the town grown.
MAX_ITEMS = 2000
MAX_TEXT = 5000


class ContractError(Exception):
    pass


def _web(v: Any) -> bool:
    return isinstance(v, str) and v.strip().lower().startswith(("http://", "https://"))


class _Checker:
    def __init__(self, name: str):
        self.name = name
        self.problems: list[str] = []

    def need(self, ok: bool, msg: str) -> None:
        if not ok:
            self.problems.append(msg)

    def done(self) -> None:
        if self.problems:
            shown = "\n  - ".join(self.problems[:25])
            more = f"\n  … and {len(self.problems) - 25} more" if len(self.problems) > 25 else ""
            raise ContractError(f"{self.name}: {len(self.problems)} contract violation(s)\n  - {shown}{more}")


def _envelope(c: _Checker, p: dict[str, Any], list_key: str) -> list[dict]:
    c.need(isinstance(p.get("generated_at"), str), "generated_at missing")
    c.need(isinstance(p.get("failures"), list), "failures must be a list")
    items = p.get(list_key)
    c.need(isinstance(items, list), f"{list_key} must be a list")
    return items if isinstance(items, list) else []


def _is_minute(v: Any) -> bool:
    if not isinstance(v, str) or not MINUTE_RX.match(v):
        return False
    try:
        datetime.fromisoformat(v)
        return True
    except ValueError:
        return False


def _is_day(v: Any) -> bool:
    if not isinstance(v, str) or not DAY_RX.match(v):
        return False
    try:
        date.fromisoformat(v)
        return True
    except ValueError:
        return False


def _unique(c: _Checker, ids: Iterable[str], what: str) -> None:
    seen: set[str] = set()
    for i in ids:
        c.need(i not in seen, f"duplicate {what} id {i!r}")
        seen.add(i)


def check_events(p: dict[str, Any]) -> None:
    c = _Checker("events.json")
    events = _envelope(c, p, "events")
    for e in events:
        eid = e.get("id")
        c.need(bool(eid), f"event without id: {e.get('title')!r}")
        c.need(bool(e.get("title")), f"{eid}: empty title")
        c.need(e.get("category") in EVENT_CATEGORIES, f"{eid}: bad category {e.get('category')!r}")
        c.need(_is_minute(e.get("start")), f"{eid}: bad start {e.get('start')!r}")
        c.need(e.get("end") is None or _is_minute(e.get("end")), f"{eid}: bad end {e.get('end')!r}")
        c.need(bool(e.get("venue")), f"{eid}: empty venue")
        c.need(bool(e.get("sourceName")), f"{eid}: empty sourceName")
        url = e.get("sourceUrl")
        c.need(url == "" or _web(url), f"{eid}: sourceUrl must be http(s) or empty, got {str(url)[:40]!r}")
        c.need(len(e.get("description") or "") <= MAX_TEXT, f"{eid}: description over {MAX_TEXT} chars")
    c.need(len(events) <= MAX_ITEMS, f"{len(events)} events, limit {MAX_ITEMS}")
    _unique(c, (e.get("id") for e in events), "event")
    c.done()


def check_news(p: dict[str, Any]) -> None:
    c = _Checker("news.json")
    items = _envelope(c, p, "items")
    for i in items:
        iid = i.get("id")
        c.need(bool(iid), f"item without id: {i.get('title')!r}")
        c.need(bool(i.get("title")), f"{iid}: empty title")
        c.need(_web(i.get("link")), f"{iid}: link must be http(s), got {str(i.get('link'))[:40]!r}")
        c.need(len(i.get("summary") or "") <= MAX_TEXT, f"{iid}: summary over {MAX_TEXT} chars")
        c.need(_is_minute(i.get("published")), f"{iid}: bad published {i.get('published')!r}")
        c.need(bool(i.get("source")), f"{iid}: empty source")
        c.need(i.get("priority") in PRIORITIES, f"{iid}: bad priority {i.get('priority')!r}")
    c.need(len(items) <= MAX_ITEMS, f"{len(items)} items, limit {MAX_ITEMS}")
    _unique(c, (i.get("id") for i in items), "news")
    c.done()


def check_sport(p: dict[str, Any]) -> None:
    c = _Checker("sport.json")
    matches = _envelope(c, p, "matches")
    teams = p.get("teams") or []
    team_ids = {t.get("id") for t in teams}
    for t in teams:
        c.need(t.get("sport") in SPORTS, f"team {t.get('id')}: bad sport {t.get('sport')!r}")
    for m in matches:
        mid = m.get("id")
        c.need(m.get("teamId") in team_ids, f"{mid}: unknown teamId {m.get('teamId')!r}")
        c.need(_is_day(m.get("date")), f"{mid}: bad date {m.get('date')!r}")
        c.need(m.get("time") is None or bool(HHMM_RX.match(str(m.get("time")))), f"{mid}: bad time {m.get('time')!r}")
        c.need(m.get("status") in MATCH_STATUSES, f"{mid}: bad status {m.get('status')!r}")
        c.need(m.get("stage", "REGULAR") in STAGES, f"{mid}: bad stage {m.get('stage')!r}")
        finished = m.get("status") == "FINISHED"
        scores = (m.get("homeScore"), m.get("awayScore"))
        if finished:
            c.need(all(isinstance(s, int) for s in scores), f"{mid}: FINISHED without both scores")
        url = m.get("url")
        c.need(url is None or str(url).startswith(("http://", "https://")), f"{mid}: url must be http(s)")
    _unique(c, (m.get("id") for m in matches), "match")
    c.done()


def check_waste(p: dict[str, Any]) -> None:
    c = _Checker("waste.json")
    rejony = _envelope(c, p, "rejony")
    for r in rejony:
        rid = r.get("id")
        c.need(bool(rid), "rejon without id")
        c.need(bool(r.get("district")), f"{rid}: empty district")
        c.need(r.get("houseType") in HOUSE_TYPES, f"{rid}: bad houseType {r.get('houseType')!r}")
        c.need(bool(r.get("streets")), f"{rid}: no streets (use \"*\" for a whole district)")
        for s in r.get("streets") or []:
            c.need(bool(s.get("name")), f"{rid}: street without name")
            for rule in s.get("rules") or []:
                c.need(rule.get("parity") in PARITIES, f"{rid}/{s.get('name')}: bad parity {rule.get('parity')!r}")
        pickups = r.get("pickups") or []
        weekday_rules = r.get("weekdayRules") or []
        c.need(not (pickups and weekday_rules), f"{rid}: both pickups and weekdayRules")
        for pk in pickups:
            c.need(pk.get("type") in WASTE_TYPES, f"{rid}: bad waste type {pk.get('type')!r}")
            dates = pk.get("dates") or []
            c.need(all(_is_day(d) for d in dates), f"{rid}/{pk.get('type')}: bad date in {dates[:3]}…")
            c.need(dates == sorted(dates), f"{rid}/{pk.get('type')}: dates not sorted")
        for wr in weekday_rules:
            c.need(wr.get("type") in WASTE_TYPES, f"{rid}: bad waste type {wr.get('type')!r}")
            c.need(all(d in WEEKDAYS for d in wr.get("weekdays") or []), f"{rid}: bad weekday in {wr.get('weekdays')}")
            c.need(wr.get("weekParity") in PARITIES, f"{rid}: bad weekParity {wr.get('weekParity')!r}")
    _unique(c, (r.get("id") for r in rejony), "rejon")
    c.done()


def check_points(p: dict[str, Any]) -> None:
    c = _Checker("waste_points.json")
    points = _envelope(c, p, "points")
    for pt in points:
        pid = pt.get("id")
        c.need(pt.get("kind") in POINT_KINDS, f"{pid}: bad kind {pt.get('kind')!r}")
        c.need(bool(pt.get("name")), f"{pid}: empty name")
        c.need(bool(pt.get("address")), f"{pid}: empty address — worse than no entry at all")
        c.need(pt.get("url", "") == "" or _web(pt.get("url")), f"{pid}: url must be http(s) or empty")
    for g in p.get("guide") or []:
        c.need(bool(g.get("item")), "guide entry without item")
        c.need(g.get("where") in GUIDE_WHERE, f"guide {g.get('item')!r}: bad where {g.get('where')!r}")
    _unique(c, (pt.get("id") for pt in points), "point")
    c.done()


def check_transit(p: dict[str, Any]) -> None:
    c = _Checker("transit_meta.json")
    c.need(str(p.get("gtfs_url", "")).startswith("https://"), "gtfs_url must be https")
    c.need(p.get("valid_to") is None or _is_day(p.get("valid_to")), "bad valid_to")
    c.need(isinstance(p.get("failures", []), list), "failures must be a list")
    c.done()
