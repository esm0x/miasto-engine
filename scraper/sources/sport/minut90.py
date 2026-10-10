"""Football from 90minut.pl. One page per club per season holds the whole season:
played matches with scores AND future fixtures with kick-off times, league and cup.

Team params: {"provider": "minut90", "clubId": 18912}. Any club on 90minut works.

Pitfalls, verified against the live source:
  * 90minut.pl speaks HTTP only — port 443 refuses the connection outright — and
    serves ISO-8859-2 while declaring it properly.
  * `id_sezon` grows by 2 per season (2021/22 = 99 … 2025/26 = 107) and the club page
    does NOT link the season in progress, so it is computed and then verified by
    checking that the matches really fall inside the season window.
"""

from __future__ import annotations

import re
import sys
import time
from datetime import date, datetime
from typing import Optional

from bs4 import BeautifulSoup

from engine.common import Ctx
from modules.sport import POLITE_DELAY, Match, Team, http_get, parse_score, season_start_year, slug

M90_BASE = "http://www.90minut.pl/mecze_druzyna.php"
# Anchor for the season arithmetic: 2025/26 was id_sezon=107, and the id grows by
# two each season. Verified against 99 = 2021/22 … 107 = 2025/26.
M90_ANCHOR_SEASON = 2025
M90_ANCHOR_ID = 107


def m90_rows(club_id: int, season_id: int) -> list[tuple[list[str], Optional[str]]]:
    """Each fixture row, plus the link to its match page when 90minut has one.

    The match page is where the detail lives — scorers with minutes, both line-ups,
    substitutions, the referee — buried at the bottom under a very long menu. The row
    also links to the opponent's season page, so the match link is picked by its path.
    """
    r = http_get(f"{M90_BASE}?id={club_id}&id_sezon={season_id}", encoding="iso-8859-2")
    soup = BeautifulSoup(r.text, "html.parser")
    rows: list[tuple[list[str], Optional[str]]] = []
    for tr in soup.find_all("tr"):
        cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        cells = [c for c in cells if c]
        if len(cells) >= 4 and re.match(r"^\d{4}-\d{2}-\d{2}", cells[0]):
            link = tr.find("a", href=re.compile(r"mecz\.php\?id_mecz=\d+"))
            url = f"http://www.90minut.pl{link['href']}" if link else None
            rows.append((cells, url))
    return rows


def resolve_m90_season(
    club_id: int, today: date,
) -> tuple[int, list[tuple[list[str], Optional[str]]]]:
    """Find the id_sezon whose matches actually fall inside the current season.

    The arithmetic alone would be a silent trap the day 90minut changes its
    numbering, so the guess is verified against the dates on the page and the
    neighbouring ids are tried before giving up.
    """
    start = season_start_year(today)
    guess = M90_ANCHOR_ID + 2 * (start - M90_ANCHOR_SEASON)
    window = (date(start, 7, 1), date(start + 1, 6, 30))

    for candidate in (guess, guess + 2, guess - 2, guess + 4, guess - 4):
        if candidate < 1:
            continue
        rows = m90_rows(club_id, candidate)
        inside = [
            r for r in rows
            if window[0] <= datetime.strptime(r[0][0][:10], "%Y-%m-%d").date() <= window[1]
        ]
        if inside:
            if candidate != guess:
                print(f"[warn] id_sezon {guess} był pusty, użyto {candidate}", file=sys.stderr)
            return candidate, inside
        time.sleep(POLITE_DELAY)

    raise RuntimeError(f"nie znalazłem sezonu {start}/{start + 1} dla klubu {club_id}")


def parse_football(team: Team, today: date) -> list[Match]:
    season_id, rows = resolve_m90_season(int(team.params['clubId']), today)
    print(f"[info] {team.name}: id_sezon={season_id}, {len(rows)} meczów", file=sys.stderr)

    out: list[Match] = []
    for cells, url in rows:
        # 90minut puts date and kick-off in one cell, and drops the time when the
        # fixture has a date but no hour yet.
        stamp = cells[0]
        day = stamp[:10]
        hour = re.search(r"\b(\d{2}:\d{2})\b", stamp)
        competition, home, score, away = cells[1], cells[2], cells[3], cells[4]

        hs, aws, note = parse_score(score)
        is_home = team.marker in home
        out.append(Match(
            id=f"{team.id}-{day}-{slug(away if is_home else home)}",
            teamId=team.id,
            competition=competition,
            date=day,
            time=hour.group(1) if hour else None,
            home=home,
            away=away,
            isHome=is_home,
            homeScore=hs,
            awayScore=aws,
            scoreNote=note,
            status="FINISHED" if hs is not None else "SCHEDULED",
            # "POkr" is the regional Puchar Polski; everything else is league football.
            stage="CUP" if competition.startswith("POkr") else "REGULAR",
            url=url,
        ))
    return out


def fetch(team: Team, ctx: Ctx, failures: list[dict]) -> list[Match]:
    return parse_football(team, ctx.today)
