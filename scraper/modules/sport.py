"""Sport fixtures and results → data/<slug>/sport.json

    "sport": {
      "teams": [
        {"id": "row-1964", "name": "ROW 1964 Rybnik", "sport": "FOOTBALL",
          "league": "III liga, gr. III", "url": "http://www.90minut.pl/skarb.php?id_klub=18912",
          "marker": "ROW 1964 Rybnik",
          "provider": "minut90", "clubId": 18912},
        {"id": "row-zuzel", "name": "INNPRO ROW Rybnik", "sport": "SPEEDWAY", ...,
          "provider": "ekstraliga", "leagues": ["m2e", "pgee"],
          "fallback": {"schedule": "https://row.rybnik.com.pl/druzyna/terminarz",
                       "home": "https://row.rybnik.com.pl/home"}}
      ]
    }

`marker` is the substring that identifies the club in a fixture cell. "ROW Rybnik"
alone would match the women's team inside the men's table and the other way round.

The notes below were written for Rybnik's clubs and still describe the providers:
Rybnik sport fixtures and results → scraper/data/sport.json

Sources:
  * 90minut.pl  — football. ROW 1964 Rybnik (men, III liga gr. III) and
                  ROW Rybnik (k) (women). One page per club per season holds the
                  whole season: played matches with scores AND future fixtures
                  with kick-off times, league and cup together.
  * ekstraliga.pl — speedway (INNPRO ROW Rybnik). The league organiser's own
                  schedule: regular season AND play-off, play-down and barrage
                  matches, each with its stage and an official match page.
  * row.rybnik.com.pl — the club's site, kept only as a fallback. It publishes the
                  regular season alone, which is why it stopped being the source.

Pitfalls, all verified against the live sources:
  * 90minut.pl speaks HTTP only — port 443 refuses the connection outright — and
    serves ISO-8859-2 while declaring it properly, so requests' own guess is fine
    but must not be overridden with UTF-8.
  * `id_sezon` on 90minut grows by 2 per season (2021/22 = 99 … 2025/26 = 107) and
    the club page does NOT link the season in progress, so it cannot be scraped
    from there. It is computed and then verified by checking that the matches
    really fall inside the season window, with neighbouring ids as fallback.
  * Football scores are not always "2-1": a walkover reads "0-3 (wo)" and a cup tie
    decided on penalties reads "0-0k. 6-7". The extra text goes to `scoreNote`.
  * Away fixtures late in the season have a date but no kick-off time yet, hence
    `time` is nullable rather than faked as 00:00.
  * Speedway play-offs used to be missing entirely: the club site titles its schedule
    "rundy zasadniczej" and stops at round 14, so the 2026 semi-final against PSŻ
    Poznań never reached the app. Testers read that as the app not marking play-offs.
    ekstraliga.pl has them, with the stage spelled out in `match_subtype`.
  * ekstraliga.pl is a Next.js app: the data is not in the markup but in the React
    Server Components stream, as escaped JSON split across self.__next_f.push chunks.
  * Its `datetime_schedule` is a UTC instant in milliseconds. Read naively it comes out
    right on a Polish laptop and two hours early on GitHub Actions, which runs in UTC,
    so it is always converted to Europe/Warsaw explicitly.
  * A match can carry a score while still running — status "W trakcie" (3) — so a
    result counts as final only on status "Rozegrany" (1), never on the score alone.
  * Two-legged ties are labelled "mecz 1" and "rewanż", and the second leg carries the
    aggregate, because a play-off result means nothing without knowing who went through.

Output shape is fixed by scraper/CONTRACT.md (sport.json) — Kotlin deserializes it
1:1, so field names and the enum values are binding.
"""

from __future__ import annotations

import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Optional

from engine.common import UA, Ctx, get, load_source, log, now_iso, write_json
from engine.common import slug as slug  # noqa: F401 — re-exported for the sources
from engine.contract import check_sport

BROWSER_HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pl-PL,pl;q=0.9",
}

POLITE_DELAY = 0.4


@dataclass(frozen=True)
class Team:
    id: str
    name: str
    sport: str          # FOOTBALL | FOOTBALL_W | SPEEDWAY
    league: str
    url: str
    marker: str
    provider: str       # sources/sport/<provider>.py
    params: dict        # everything else from the team's entry, for the provider

    @staticmethod
    def from_config(raw: dict) -> "Team":
        known = {"id", "name", "sport", "league", "url", "marker", "provider"}
        return Team(
            id=raw["id"], name=raw["name"], sport=raw["sport"], league=raw["league"],
            url=raw["url"], marker=raw.get("marker") or raw["name"], provider=raw["provider"],
            params={k: v for k, v in raw.items() if k not in known},
        )

    def to_json(self) -> dict:
        return {"id": self.id, "name": self.name, "sport": self.sport,
                "league": self.league, "url": self.url}


@dataclass
class Match:
    id: str
    teamId: str
    competition: str
    date: str                       # YYYY-MM-DD
    time: Optional[str]             # HH:MM, null when the kick-off is not set yet
    home: str
    away: str
    isHome: bool
    homeScore: Optional[int]
    awayScore: Optional[int]
    scoreNote: Optional[str]        # "wo", "k. 6-7", "dwumecz 87:93" — beyond the plain score
    status: str                     # SCHEDULED | FINISHED
    stage: str = "REGULAR"          # REGULAR | PLAYOFF | PLAYDOWN | BARRAGE | CUP
    url: Optional[str] = None       # match page with the full result, for the app to open


def http_get(url: str, encoding: Optional[str] = None):
    """GET with a short retry; one dead source must not kill the run."""
    return get(url, headers=BROWSER_HEADERS, retries=2, encoding=encoding)


def season_start_year(today: date) -> int:
    """Polish seasons run summer to summer, so July flips the year over."""
    return today.year if today.month >= 7 else today.year - 1


def parse_score(raw: str) -> tuple[Optional[int], Optional[int], Optional[str]]:
    """'2-1' → (2, 1, None); '0-3 (wo)' → (0, 3, 'wo'); '0-0k. 6-7' → (0, 0, 'k. 6-7')."""
    text = raw.strip()
    m = re.match(r"^(\d+)\s*[-:]\s*(\d+)(.*)$", text)
    if not m:
        return None, None, None
    note = m.group(3).strip(" ()").strip()
    return int(m.group(1)), int(m.group(2)), note or None


def report(matches: list[Match], teams: list[Team], today: date) -> None:
    for team in teams:
        mine = [m for m in matches if m.teamId == team.id]
        played = [m for m in mine if m.status == "FINISHED"]
        ahead = [m for m in mine if m.status == "SCHEDULED" and m.date >= today.isoformat()]
        nxt = min((m.date for m in ahead), default=None)
        print(
            f"[info] {team.name}: {len(mine)} meczów "
            f"({len(played)} rozegranych, najbliższy: {nxt or 'brak — po sezonie'})",
            file=sys.stderr,
        )
        if not mine:
            print(f"[warn] ZERO meczów dla {team.name} — parser albo źródło się zmieniło",
                  file=sys.stderr)


def run(ctx: Ctx) -> dict:
    cfg = ctx.module("sport") or {}
    teams = [Team.from_config(t) for t in cfg.get("teams", [])]
    today = ctx.today
    out_path = ctx.data_dir / "sport.json"

    matches: list[Match] = []
    failures: list[dict] = []

    for team in teams:
        try:
            log(f"[info] {team.name}: {team.provider}")
            # A provider may record a partial failure itself (its primary source died
            # and it fell back to a worse one) and still return matches.
            matches.extend(load_source("sport", team.provider).fetch(team, ctx, failures))
        except Exception as e:  # noqa: BLE001 — one dead source must not kill the run
            log(f"[error] {team.name}: {e}")
            failures.append({"source": team.name, "error": str(e)})
        time.sleep(POLITE_DELAY)

    matches.sort(key=lambda m: (m.date, m.time or "99:99"))
    report(matches, teams, today)

    payload = {
        "generated_at": now_iso(),
        "count": len(matches),
        "failures": failures,
        "teams": [t.to_json() for t in teams],
        "matches": [asdict(m) for m in matches],
    }
    check_sport(payload)
    write_json(out_path, payload)
    log(f"[info] wrote {len(matches)} matches (failures: {len(failures)}) → {out_path}")
    return payload
