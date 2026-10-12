"""A GTFS zip the city links from one of its pages, under a name that changes per edition.

Params:
    {"page": "https://www.zory.pl/dla-mieszkancow/bezplatna-komunikacja-miejska",
     "linkPattern": "GTFS[^/]*\\.zip$", "hosts": ["zory.pl"]}

Żory puts each edition up as GTFS_<dd_mm_yy>.zip and links it from the BKM page, so the
URL is found again every run. The zip is copied to data/<slug>/gtfs.zip and the app
downloads that copy: the checksum in transit_meta.json then always describes the file
behind gtfs_url, and an edition the city replaces under the same name cannot reach
phones half-checked.

The copy is not the city's bytes. It is a new zip of the root GTFS files only, each
under a size limit: a hostile zip could carry a few-gigabyte stop_times.txt that
compresses to megabytes, or a second "x/stops.txt" that the app, reading names after
the last slash, would take instead of the file checked here.

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
KEPT = REQUIRED + ["calendar.txt", "calendar_dates.txt", "feed_info.txt", "shapes.txt"]
MAX_ZIP = 20 * 1024 * 1024
MAX_MEMBER = 64 * 1024 * 1024      # Żory: stop_times.txt is 0.8 MB, Rybnik's 9 MB
MAX_TOTAL = 200 * 1024 * 1024


# "CENTRUM PRZESIADKOWE przez:" and "BOCZNA-KLONOWA p.": the R&G export leaves the via
# part of a headsign empty and keeps its label, which the departure board then shows.
TRAILING_VIA = re.compile(r"\s+(?:przez:?|p\.)\s*$", re.IGNORECASE)


def tidy_headsigns(data: bytes) -> bytes:
    import csv

    text = data.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(text)))
    if not rows or "trip_headsign" not in rows[0]:
        return data
    col = rows[0].index("trip_headsign")
    for r in rows[1:]:
        if len(r) > col:
            r[col] = TRAILING_VIA.sub("", r[col])
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows(rows)
    return buf.getvalue().encode("utf-8")


def find_link(page: str, pattern: str, hosts: list[str]) -> str:
    html = get(page, headers={"User-Agent": UA}, retries=2, allowed_hosts=tuple(hosts)).text
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
    original = get(url, headers={"User-Agent": UA}, timeout=120, retries=2, max_bytes=MAX_ZIP,
                   allowed_hosts=tuple(params["hosts"])).content

    source = zipfile.ZipFile(io.BytesIO(original))
    infos = source.infolist()
    if sum(i.file_size for i in infos) > MAX_TOTAL or any(i.file_size > MAX_MEMBER for i in infos):
        raise RuntimeError("GTFS zip members over the size limit")
    # Root files only, each once; anything in a folder is ignored and not published.
    root = {i.filename: i for i in infos if "/" not in i.filename and "\\" not in i.filename}
    blob = io.BytesIO()
    with zipfile.ZipFile(blob, "w", zipfile.ZIP_DEFLATED) as out:
        for name in KEPT:
            if name in root:
                data = source.read(root[name])
                # A fixed timestamp keeps the zip byte-identical between runs: its sha256 is
                # the app's edition key, and a new one every six hours would re-import the
                # timetable on every phone and commit gtfs.zip on every run.
                info = zipfile.ZipInfo(name, date_time=(2000, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                out.writestr(info, tidy_headsigns(data) if name == "trips.txt" else data)
    blob = blob.getvalue()
    zf = zipfile.ZipFile(io.BytesIO(blob))
    names = set(zf.namelist())
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
