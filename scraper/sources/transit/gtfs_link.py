"""A GTFS zip the city links from one of its pages, under a name that changes per edition.

Params:
    {"page": "https://www.zory.pl/dla-mieszkancow/bezplatna-komunikacja-miejska",
     "linkPattern": "GTFS[^/]*\\.zip$", "hosts": ["zory.pl"]}

Żory puts each edition up as GTFS_<dd_mm_yy>.zip and links it from the BKM page, so the
URL is found again every run. The zip is copied to data/<slug>/gtfs.zip and the app
downloads that copy: the checksum in transit_meta.json then always describes the file
behind gtfs_url, and an edition the city replaces under the same name cannot reach
phones half-checked.

The feed is written by R&G (municom), like KM Rybnik's: calendar.txt with every weekday
flag 0 and the real service in calendar_dates.txt. The app's reader copes; a feed with
no calendar_dates rows at all would leave it with no departures, so that is a failure.
"""

from __future__ import annotations

import hashlib
import io
import re
import zipfile
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from engine.common import UA, Ctx, get, log, now_iso, same_site
from sources.transit.km_rybnik import read_rows, validity_window

REQUIRED = ["agency.txt", "stops.txt", "routes.txt", "trips.txt", "stop_times.txt"]
MAX_ZIP = 20 * 1024 * 1024


def find_link(page: str, pattern: str, hosts: list[str]) -> str:
    html = get(page, headers={"User-Agent": UA}, retries=2).text
    rx = re.compile(pattern, re.IGNORECASE)
    for a in BeautifulSoup(html, "html.parser").select("a[href]"):
        url = urljoin(page, a["href"])
        if rx.search(url) and same_site(url, *hosts) and url.startswith("https://"):
            return url
    raise RuntimeError(f"no link matching {pattern!r} on {page}")


def fetch(params: dict, ctx: Ctx) -> dict:
    failures: list[dict] = []
    url = find_link(params["page"], params.get("linkPattern", r"gtfs[^/]*\.zip$"), params["hosts"])
    log(f"[info] GTFS: {url}")
    blob = get(url, headers={"User-Agent": UA}, timeout=120, retries=2).content
    if len(blob) > MAX_ZIP:
        raise RuntimeError(f"GTFS zip of {len(blob)} B is over {MAX_ZIP} B")

    zf = zipfile.ZipFile(io.BytesIO(blob))
    names = set(zf.namelist())
    # A zip is a list of paths someone else chose; nothing here is extracted, but a
    # member like "../x" or "/x" says the file is not what it claims to be.
    if any(n.startswith(("/", "\\")) or ".." in n.replace("\\", "/").split("/") for n in names):
        raise RuntimeError("GTFS zip has member paths outside its root")
    missing = [m for m in REQUIRED if m not in names]
    if missing:
        raise RuntimeError(f"GTFS without {', '.join(missing)}")
    if "calendar.txt" not in names and "calendar_dates.txt" not in names:
        raise RuntimeError("GTFS without calendar.txt or calendar_dates.txt")

    stops = read_rows(zf, "stops.txt")
    routes = read_rows(zf, "routes.txt")
    active = [r for r in read_rows(zf, "calendar_dates.txt") if (r.get("exception_type") or "").strip() == "1"] \
        if "calendar_dates.txt" in names else []
    calendar_days = any(any((r.get(d) or "0").strip() == "1" for d in
                            ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"))
                        for r in read_rows(zf, "calendar.txt")) if "calendar.txt" in names else False
    if not active and not calendar_days:
        failures.append({"source": url, "error": "no service days in calendar.txt or calendar_dates.txt"})
    if not stops or not routes:
        raise RuntimeError("stops.txt or routes.txt is empty")

    valid_from, valid_to = validity_window(zf, failures)
    if valid_to and valid_to < ctx.today.isoformat():
        failures.append({"source": url, "error": f"rozkład ważny tylko do {valid_to}; miasto nie wystawiło nowego"})

    (ctx.data_dir / "gtfs.zip").write_bytes(blob)
    log(f"[info] GTFS: {len(stops)} przystanków, {len(routes)} linii, {valid_from}…{valid_to}, {len(blob)} B")
    return {
        "generated_at": now_iso(),
        "gtfs_url": ctx.city["dataBaseUrl"] + "gtfs.zip",
        "attachment_id": None,
        "valid_from": valid_from,
        "valid_to": valid_to,
        "stop_count": len(stops),
        "route_count": len(routes),
        "sha256": hashlib.sha256(blob).hexdigest(),
        "editions": [url.rsplit("/", 1)[-1]],
        "failures": failures,
    }
