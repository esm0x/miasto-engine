"""Polish public holidays and school days: what a timetable's day types are made of.

Polish bus timetables split weekdays into "w dni nauki szkolnej" and "w dni wolne od
nauki szkolnej", and every type ends with "oprócz świąt". Turning those into dates
needs two things that are not in any timetable:

  * public holidays, computed here (the fixed ones, Easter and what hangs off it). Since
    2025 Wigilia, 24 December, is a public holiday too (Dz.U. 2024 poz. 1965).
  * the school calendar of the voivodeship: start and end of the school year and the
    breaks, which the city's sources.json lists from the MEN regulation. Winter holidays
    differ by voivodeship, so they cannot be computed and must not be guessed.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable


def easter(year: int) -> date:
    """Anonymous Gregorian algorithm (Meeus/Jones/Butcher)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def public_holidays(year: int) -> set[date]:
    fixed = [(1, 1), (1, 6), (5, 1), (5, 3), (8, 15), (11, 1), (11, 11), (12, 25), (12, 26)]
    if year >= 2025:
        fixed.append((12, 24))
    out = {date(year, m, d) for m, d in fixed}
    e = easter(year)
    out |= {e, e + timedelta(days=1), e + timedelta(days=49), e + timedelta(days=60)}
    return out


class SchoolCalendar:
    """Which weekdays are school days, from the ranges given in sources.json.

        {"schoolYears": [["2026-09-01", "2027-06-25"]],
         "breaks": [["2026-12-23", "2026-12-31"], ["2027-01-18", "2027-01-31"], …],
         "knownUntil": "2027-08-31"}

    `knownUntil` bounds what the calendar can answer: past it a feed must not claim to
    know which days are school days, so the generated service stops there.
    """

    def __init__(self, cfg: dict):
        self.years = [(date.fromisoformat(a), date.fromisoformat(b)) for a, b in cfg["schoolYears"]]
        self.breaks = [(date.fromisoformat(a), date.fromisoformat(b)) for a, b in cfg.get("breaks", [])]
        self.known_until = date.fromisoformat(cfg["knownUntil"])

    def is_school_day(self, d: date) -> bool:
        if d.weekday() >= 5 or d in public_holidays(d.year):
            return False
        if not any(a <= d <= b for a, b in self.years):
            return False
        return not any(a <= d <= b for a, b in self.breaks)


# Day-type keys used as GTFS service ids.
SCHOOL = "szkolne"            # Mon-Fri school days, not holidays
SCHOOL_FREE = "wolne-od-nauki"  # Mon-Fri without school, not holidays
WEEKDAYS = "robocze"          # Mon-Fri, not holidays
SATURDAY = "soboty"           # Saturdays, not holidays
SUNDAY = "niedziele-swieta"   # Sundays and holidays
WEEKEND = "weekend"           # Saturdays, Sundays, holidays
DAILY = "codziennie"


def day_type(label: str) -> str | None:
    """'Od poniedziałku do piątku - w dni nauki szkolnej oprócz świąt' → SCHOOL.

    None for a label not understood: such trips are left out and reported, rather than
    run on days nobody can vouch for.
    """
    t = " ".join(label.lower().split())
    if "codziennie" in t:
        return DAILY
    weekday = "poniedział" in t or "robocz" in t
    if weekday and "wolne od nauki" in t:
        return SCHOOL_FREE
    if weekday and "nauki szkolnej" in t:
        return SCHOOL
    if weekday:
        return WEEKDAYS
    if "sobot" in t and ("niedziel" in t or "święt" in t):
        return WEEKEND
    if "sobot" in t:
        return SATURDAY
    if "niedziel" in t or "święt" in t:
        return SUNDAY
    return None


def service_dates(kind: str, start: date, end: date, school: SchoolCalendar) -> list[date]:
    out = []
    d = start
    while d <= end:
        holiday = d in public_holidays(d.year)
        wd = d.weekday()
        if kind == DAILY:
            ok = True
        elif kind in (SCHOOL, SCHOOL_FREE, WEEKDAYS):
            ok = wd < 5 and not holiday and (
                kind == WEEKDAYS
                or (kind == SCHOOL and school.is_school_day(d))
                or (kind == SCHOOL_FREE and not school.is_school_day(d))
            )
        elif kind == SATURDAY:
            ok = wd == 5 and not holiday
        elif kind == SUNDAY:
            ok = wd == 6 or holiday
        elif kind == WEEKEND:
            ok = wd >= 5 or holiday
        else:
            ok = False
        if ok:
            out.append(d)
        d += timedelta(days=1)
    return out


def daterange_ok(dates: Iterable[date]) -> bool:
    return all(isinstance(d, date) for d in dates)
