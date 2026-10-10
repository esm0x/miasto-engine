"""Speedway from ekstraliga.pl, the league organiser's own schedule: regular season AND
play-off, play-down and barrage matches, each with its stage and an official match page.

Team params:
    {"provider": "ekstraliga", "leagues": ["m2e", "pgee"],
     "fallback": {"schedule": "https://row.rybnik.com.pl/druzyna/terminarz",
                  "home": "https://row.rybnik.com.pl/home"}}   # optional

Both leagues are searched instead of hard-coding the current one, so promotion or
relegation needs no change. The fallback is a club site with the regular season only
(table + results slider in the markup of row.rybnik.com.pl); used when ekstraliga.pl
fails, and recorded as a failure so the degraded data is visible.

Pitfalls, verified against the live source:
  * ekstraliga.pl is a Next.js app: the data is not in the markup but in the React
    Server Components stream, as escaped JSON split across self.__next_f.push chunks.
  * Its `datetime_schedule` is a UTC instant in milliseconds. Read naively it comes out
    right on a Polish laptop and two hours early on GitHub Actions, which runs in UTC,
    so it is always converted to Europe/Warsaw explicitly.
  * A match can carry a score while still running — status "W trakcie" (3) — so a
    result counts as final only on status "Rozegrany" (1), never on the score alone.
  * Two-legged ties are labelled "mecz 1" and "rewanż", and the second leg carries the
    aggregate, because a play-off result means nothing without knowing who went through.
"""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import date, datetime
from typing import Optional
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from engine.common import PL_MONTHS, Ctx, log
from modules.sport import POLITE_DELAY, Match, Team, http_get, parse_score, slug

EKSTRALIGA = "https://ekstraliga.pl"
WARSAW = ZoneInfo("Europe/Warsaw")
EKSTRALIGA_FINISHED = 1


def rsc_payload(page: str) -> str:
    """The data behind a Next.js page: escaped string chunks, joined and unescaped."""
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', page, re.S)
    return "".join(json.loads('"' + c + '"') for c in chunks)


def json_objects_after(text: str, key: str) -> list[dict]:
    """Every JSON object that opens right after `key`, found by matching braces.

    The objects sit inside a larger structure that is not itself valid JSON, so they
    are cut out one at a time rather than parsed as a whole.
    """
    found: list[dict] = []
    start = 0
    while (at := text.find(key, start)) >= 0:
        open_at = text.find("{", at + len(key) - 1)
        depth = 0
        for i in range(open_at, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        found.append(json.loads(text[open_at:i + 1]))
                    except json.JSONDecodeError:
                        pass
                    break
        start = at + len(key)
    return found


def league_events(league: str, season: int) -> list[dict]:
    page = http_get(f"{EKSTRALIGA}/se/terminarz-i-wyniki/{league}/{season}").text
    return json_objects_after(rsc_payload(page), '"event":{')


def speedway_stage(subtype: str) -> str:
    folded = subtype.lower()
    if "play-off" in folded:
        return "PLAYOFF"
    if "play-down" in folded:
        return "PLAYDOWN"
    if "bara" in folded:
        return "BARRAGE"
    return "REGULAR"


def speedway_round_label(subtype: str, round_no: Optional[int], stage: str) -> str:
    """'Runda 7' in the regular season; the tie itself otherwise.

    The league's own short names ("o 5-6 msc") read like a spreadsheet header, so the
    full name is turned into something a person would say instead.
    """
    if stage == "REGULAR":
        return f"Runda {round_no}" if round_no else "Runda zasadnicza"
    if stage == "BARRAGE":
        return "Baraż"
    detail = subtype.split(" - ", 1)[-1].strip()
    if detail.lower().startswith("półfina"):
        return "Półfinał"
    if detail.lower().startswith("fina"):
        return "Finał"
    place = re.search(r"o\s*(\d+)", detail)
    return f"Mecz o {place.group(1)}. miejsce" if place else detail


def build_speedway(team: Team, events: list[dict], league: str, season: int) -> list[Match]:
    out: list[Match] = []
    for e in events:
        home, away = (part.strip() for part in e["name"]["pl"].split(" - ", 1))
        sides = {t.get("no"): t for t in e.get("card_teams") or []}
        finished = (e.get("status") or {}).get("id") == EKSTRALIGA_FINISHED
        hs = sides.get(1, {}).get("match_score") if finished else None
        aws = sides.get(2, {}).get("match_score") if finished else None

        when = datetime.fromtimestamp(e["datetime_schedule"] / 1000, WARSAW)
        subtype = ((e.get("match_subtype") or {}).get("name") or {}).get("pl", "")
        stage = speedway_stage(subtype)
        is_home = team.marker in home

        out.append(Match(
            id=f"{team.id}-{when:%Y-%m-%d}-{slug(away if is_home else home)}",
            teamId=team.id,
            competition=speedway_round_label(subtype, e.get("round"), stage),
            date=f"{when:%Y-%m-%d}",
            time=f"{when:%H:%M}",
            home=home,
            away=away,
            isHome=is_home,
            homeScore=hs,
            awayScore=aws,
            scoreNote=None,
            status="FINISHED" if hs is not None and aws is not None else "SCHEDULED",
            stage=stage,
            url=f"{EKSTRALIGA}/se/mecz/{e['id']}",
        ))
    label_two_legged_ties(out)
    print(f"[info] {team.name}: {league}/{season}, {len(out)} meczów, "
          f"w tym {sum(m.stage != 'REGULAR' for m in out)} poza rundą zasadniczą",
          file=sys.stderr)
    return out


def label_two_legged_ties(matches: list[Match]) -> None:
    """Mark the legs and, once both are played, give the second one the aggregate.

    Play-off ties are home-and-away against the same opponent. "48:42" on its own
    says nothing about who went through; "39:51, dwumecz 87:93" does.
    """
    ties: dict[tuple[str, str, str], list[Match]] = {}
    for m in matches:
        if m.stage == "REGULAR":
            continue
        opponent = m.away if m.isHome else m.home
        ties.setdefault((m.stage, m.competition, opponent), []).append(m)

    for legs in ties.values():
        if len(legs) != 2:
            continue
        first, second = sorted(legs, key=lambda m: (m.date, m.time or ""))
        first.competition += ", mecz 1"
        second.competition += ", rewanż"
        if first.status == second.status == "FINISHED":
            ours = sum((m.homeScore if m.isHome else m.awayScore) or 0 for m in legs)
            theirs = sum((m.awayScore if m.isHome else m.homeScore) or 0 for m in legs)
            second.scoreNote = f"dwumecz {ours}:{theirs}"


def parse_speedway_league(team: Team, today: date) -> list[Match]:
    """This year's schedule, or last year's while the new one is not out yet.

    Speedway runs April to September on the calendar year, so from October until the
    league publishes next season's fixtures, the season just finished is the latest
    there is, and it is better shown than an empty screen.
    """
    for season in (today.year, today.year - 1):
        for league in team.params.get("leagues", ["pge", "m1e", "m2e"]):
            events = league_events(league, season)
            mine = [e for e in events if team.marker in ((e.get("name") or {}).get("pl") or "")]
            if mine:
                return build_speedway(team, mine, league, season)
            time.sleep(POLITE_DELAY)
    raise RuntimeError(
        f"brak meczów {team.name} w {'/'.join(team.params.get('leagues', []))} "
        f"za {today.year} i {today.year - 1}"
    )


# --------------------------------------------------------------------------
# club site — the fallback
# --------------------------------------------------------------------------

def parse_speedway_schedule(team: Team) -> list[Match]:
    """The official table: round, date + time, both clubs, score. Regular season only."""
    r = http_get(team.params["fallback"]["schedule"])
    soup = BeautifulSoup(r.text, "html.parser")
    out: list[Match] = []

    for tr in soup.select("table.timetable-table tbody tr"):
        rnd = tr.select_one("td.timetable")
        when = tr.select("td.timetable")
        teams = tr.select("td.timetable-team")
        result = tr.select_one("td.timetable-result")
        if len(when) < 2 or len(teams) < 2:
            continue

        stamp = when[1].get_text("\n", strip=True)
        day = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", stamp)
        if not day:
            continue
        iso = f"{day.group(3)}-{day.group(2)}-{day.group(1)}"
        hour = re.search(r"\b(\d{1,2}:\d{2})\b", stamp)

        home = teams[0].get_text(" ", strip=True)
        away = teams[1].get_text(" ", strip=True)
        hs, aws, note = parse_score(result.get_text(" ", strip=True) if result else "")
        is_home = team.marker in home
        out.append(Match(
            id=f"{team.id}-{iso}-{slug(away if is_home else home)}",
            teamId=team.id,
            competition=rnd.get_text(" ", strip=True) if rnd else team.league,
            date=iso,
            time=hour.group(1) if hour else None,
            home=home,
            away=away,
            isHome=is_home,
            homeScore=hs,
            awayScore=aws,
            scoreNote=note,
            status="FINISHED" if hs is not None else "SCHEDULED",
        ))
    return out


def parse_speedway_extra(team: Team) -> list[Match]:
    """Results slider on the front page.

    Dates come as Polish prose ("6 września 2026, godz. 15:15"), and the markup is
    a carousel rather than a table, so each slide is read on its own. In 2026 it
    carried nothing the schedule table did not already have — it is parsed as cheap
    insurance in case the club starts posting play-off results there.
    """
    r = http_get(team.params["fallback"]["home"])
    soup = BeautifulSoup(r.text, "html.parser")
    out: list[Match] = []

    for slide in soup.select(".previous-slider .slide, .previous-match .slide"):
        text = slide.get_text(" ", strip=True)
        when = re.search(r"(\d{1,2})\s+([a-ząćęłńóśźż]+)\s+(\d{4})", text, re.I)
        score = re.search(r"\b(\d{1,3})\s*:\s*(\d{1,3})\b", text)
        names = [n.get_text(" ", strip=True) for n in slide.select(".logo-box-name")]
        if not (when and score and len(names) >= 2):
            continue
        month = PL_MONTHS.get(when.group(2).lower())
        if not month:
            continue
        iso = f"{when.group(3)}-{month:02d}-{int(when.group(1)):02d}"
        hour = re.search(r"godz\.\s*(\d{1,2}:\d{2})", text)

        home, away = names[0], names[1]
        is_home = team.marker in home
        out.append(Match(
            id=f"{team.id}-{iso}-{slug(away if is_home else home)}",
            teamId=team.id,
            competition=team.league,
            date=iso,
            time=hour.group(1) if hour else None,
            home=home,
            away=away,
            isHome=is_home,
            homeScore=int(score.group(1)),
            awayScore=int(score.group(2)),
            scoreNote=None,
            status="FINISHED",
        ))
    return out


def merge(primary: list[Match], extra: list[Match]) -> list[Match]:
    """Schedule wins on competition names; the slider only adds what it misses."""
    known = {(m.date, m.teamId) for m in primary}
    added = [m for m in extra if (m.date, m.teamId) not in known]
    if added:
        print(f"[info] żużel: {len(added)} meczów spoza rundy zasadniczej", file=sys.stderr)
    return primary + added


def fetch(team: Team, ctx: Ctx, failures: list[dict]) -> list[Match]:
    try:
        log(f"[info] scraping {EKSTRALIGA} dla {team.name}")
        return parse_speedway_league(team, ctx.today)
    except Exception as e:  # noqa: BLE001 — the club site is the fallback
        if not team.params.get("fallback"):
            raise
        # Worse data, but some data: regular season only, no match pages.
        log(f"[warn] ekstraliga.pl: {e}; awaryjnie strona klubu")
        failures.append({"source": "ekstraliga.pl", "error": str(e)})
        scheduled = parse_speedway_schedule(team)
        try:
            scheduled = merge(scheduled, parse_speedway_extra(team))
        except Exception as e2:  # noqa: BLE001 — the slider is a bonus
            log(f"[warn] slider na /home: {e2}")
        return scheduled
