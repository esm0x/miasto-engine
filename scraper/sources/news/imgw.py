"""Official IMGW weather and hydrological warnings, from the public JSON API.

Params:
    {"name": "IMGW",
     "teryt": "2473",           # powiat code, 4 digits. Verify against the GUS TERYT
                                # register, never guess it from the voivodeship code.
     "voivodeship": "śląskie"}  # for hydro warnings, which have no powiat codes

Works for every place in Poland unchanged, which makes it the cheapest alert source a
new city can have.

Two endpoints with different shapes, and the difference matters:

  * meteo warnings carry `teryt`, a list of powiat codes, so they can be matched to the
    city exactly. A gale warning for the coast lists dozens of codes and simply will not
    contain ours.
  * hydro warnings carry `obszary` with catchment codes instead, which cannot be
    resolved to a city without a river map. They are matched on the voivodeship and
    labelled as regional in the title, rather than pretending to be local.

Warnings that have already expired are dropped: `obowiazuje_do` is what makes an
alert current, and the news module has no other way to age these out.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Optional

from engine.common import Ctx, strip_html, truncate
from modules.news import PRIORITY_ALERT, SUMMARY_LEN, NewsItem, http_get

IMGW_METEO = "https://danepubliczne.imgw.pl/api/data/warningsmeteo"
IMGW_HYDRO = "https://danepubliczne.imgw.pl/api/data/warningshydro"


def _imgw_json(url: str) -> list[dict]:
    """The API answers 200 with a dict message when there is nothing to report."""
    payload = http_get(url).json()
    return payload if isinstance(payload, list) else []


def _imgw_item(raw: dict, title: str, link: str, now: datetime) -> Optional[NewsItem]:
    until = raw.get("obowiazuje_do") or raw.get("data_do") or ""
    if until and not until.startswith("9999"):
        try:
            if datetime.strptime(until[:19], "%Y-%m-%d %H:%M:%S") < now:
                return None
        except ValueError:
            pass

    # IMGW marks open-ended warnings, mostly droughts, with the year 9999. Printing that
    # date verbatim reads like a bug, so an open-ended warning simply says nothing.
    open_ended = until.startswith("9999")

    published = (raw.get("opublikowano") or "")[:16].replace(" ", "T")
    if len(published) != 16:
        published = now.isoformat(timespec="minutes")

    level = raw.get("stopien") or raw.get("stopień") or ""
    body = strip_html(raw.get("tresc") or raw.get("przebieg") or "")
    summary = truncate(
        " ".join(filter(None, [
            f"Stopień {level}." if level and level.isdigit() else "",
            f"Obowiązuje do {until[:16]}." if until and not open_ended else "",
            body,
        ])).strip(),
        SUMMARY_LEN,
    )

    # The id has to stay stable between runs, and IMGW's own id does exactly that.
    identifier = raw.get("id") or hashlib.sha1(
        (title + published).encode("utf-8")
    ).hexdigest()

    return NewsItem(
        id=f"imgw-{identifier}",
        title=title,
        summary=summary,
        link=link,
        published=published,
        source="IMGW",
        category="Ostrzeżenia",
        priority=PRIORITY_ALERT,
    )


def fetch(params: dict, ctx: Ctx, failures: list[dict]) -> list[NewsItem]:
    teryt = str(params["teryt"])
    voivodeship = params["voivodeship"]
    now = datetime.now()
    items: list[NewsItem] = []

    for raw in _imgw_json(IMGW_METEO):
        if teryt not in (raw.get("teryt") or []):
            continue
        item = _imgw_item(raw, f"IMGW: {raw.get('nazwa_zdarzenia', 'ostrzeżenie')}", IMGW_METEO, now)
        if item:
            items.append(item)

    for raw in _imgw_json(IMGW_HYDRO):
        areas = raw.get("obszary") or []
        if not any(a.get("wojewodztwo") == voivodeship for a in areas):
            continue
        item = _imgw_item(
            raw, f"IMGW (region): {raw.get('zdarzenie', 'ostrzeżenie hydrologiczne')}", IMGW_HYDRO, now,
        )
        if item:
            items.append(item)

    return items
