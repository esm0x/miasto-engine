"""A GTFS feed built from a Trasownik timetable site, for operators that publish none.

Trasownik (osm.trasownik.pl in the map, "Wybierz widok » tabelaryczny" on stop pages)
generates timetable websites for many Polish counties; Lubomia's buses are on
rozklady.powiatwodzislawski.pl. No GTFS is published for them anywhere: not on the
site, not on dane.gov.pl, not on the national access point (checked October 2026). The
site does, however, know every trip: each departure on a stop page calls
kurs.php?kat=<edition>&kier=<dir>&nr=<stop>&kurs=<n>, which returns the whole trip with
its day type and every stop's time, terminal arrival included. So nothing is
reconstructed or guessed; trips are collected, not inferred.

Params:
    {"type": "trasownik", "base": "https://rozklady.powiatwodzislawski.pl/",
     "agency": "Wodzisławska Komunikacja Powiatowa",
     "linesVia": "LUBOMIA|SYRYNIA|BUKÓW|NIEBOCZOWY|GRABÓWKA",   # keep lines touching these
     "extraCa": ["certum_dv_tls_g2_r39.pem"],                    # see engine.common.ca_bundle
     "calendar": {...},                                           # see engine.plcalendar
     "horizonDays": 150}

Cost: one request per stop page plus one per distinct trip, about 600 for Lubomia's
three lines. Paid only when the timetable edition changes: the trips are cached in
data/<slug>/transit_source.json with the editions they came from, and a run whose
editions are unchanged rebuilds the feed from the cache with one request.

The feed is deterministic: the same timetable and the same month give a byte-identical
zip, because the app re-imports whenever the sha256 changes.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import time
import zipfile
from collections import defaultdict
from datetime import date, timedelta
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from engine import plcalendar as cal
from engine.common import UA, Ctx, ca_bundle, get, log, now_iso

HEADERS = {"User-Agent": UA, "Accept-Language": "pl-PL,pl;q=0.9"}
XHR = {**HEADERS, "X-Requested-With": "XMLHttpRequest"}
POLITE = 0.25
LINE_RX = re.compile(r"start-(\d+)_(\d{8})-1\.html")
STOP_PAGE_RX = re.compile(r"rozklad-(\d+_\d{8})-(\d+)-(\d+)\.html$")
KURS_RX = re.compile(r"kurs\('([^']+)',\s*(\d+),\s*(\d+),\s*(\d+)\)")
TIME_RX = re.compile(r"^(\d{1,2}):(\d{2})")


class Site:
    def __init__(self, base: str, extra_ca: list[str]):
        self.base = base if base.endswith("/") else base + "/"
        self.verify = ca_bundle(*extra_ca) if extra_ca else True
        self.requests = 0

    def html(self, path: str, params: Optional[dict] = None, xhr: bool = False) -> BeautifulSoup:
        self.requests += 1
        r = get(urljoin(self.base, path), headers=XHR if xhr else HEADERS, params=params,
                retries=2, verify=self.verify)
        r.encoding = "utf-8"
        time.sleep(POLITE)
        return BeautifulSoup(r.text, "html.parser")


def lines_index(site: Site) -> dict[str, dict]:
    """{"041_20260412": {"line": "41", "name": "WODZISŁAW ŚL. - SYRYNIA - LUBOMIA - RACIBÓRZ"}}"""
    page = site.html("")
    out: dict[str, dict] = {}
    for a in page.select("a[href]"):
        m = LINE_RX.search(a["href"])
        if not m:
            continue
        edition = f"{m.group(1)}_{m.group(2)}"
        text = " ".join(a.get_text(" ", strip=True).split())
        entry = out.setdefault(edition, {"line": str(int(m.group(1))), "name": ""})
        if text and not text.isdigit() and len(text) > len(entry["name"]):
            entry["name"] = text
    return out


def line_stops(site: Site, edition: str) -> dict[int, list[tuple[int, str]]]:
    """Per direction, the stop pages in order: {1: [(seq, name), …], 2: […]}."""
    page = site.html(f"start-{edition}-1.html")
    dirs: dict[int, dict[int, str]] = defaultdict(dict)
    for a in page.select("a[href]"):
        m = STOP_PAGE_RX.search(a["href"])
        if m and m.group(1) == edition:
            dirs[int(m.group(3))][int(m.group(2))] = " ".join(a.get_text(" ", strip=True).split())
    return {d: sorted(stops.items()) for d, stops in dirs.items()}


def parse_trip(page: BeautifulSoup) -> tuple[str, list[tuple[str, str, int]]]:
    """kurs.php → (day-type label, [(stop_id, name, minutes after midnight)])."""
    label_el = page.select_one(".day_type")
    label = " ".join(label_el.get_text(" ", strip=True).split()) if label_el else ""
    rows: list[tuple[str, str, int]] = []
    last = -1
    for tr in page.select("tr"):
        link = tr.select_one('a[href^="przystanek-"]')
        cells = tr.select("td")
        if not link or len(cells) < 2:
            continue
        m = TIME_RX.match(cells[-1].get_text(strip=True))
        if not m:
            continue
        minutes = int(m.group(1)) * 60 + int(m.group(2))
        # A trip that crosses midnight keeps counting: GTFS writes 24:15, not 00:15.
        while minutes < last:
            minutes += 24 * 60
        last = minutes
        stop_id = link["href"].removeprefix("przystanek-").removesuffix(".html")
        rows.append((stop_id, " ".join(link.get_text(" ", strip=True).split()), minutes))
    return label, rows


def collect_trips(site: Site, edition: str, direction: int, stops: list[tuple[int, str]]) -> list[dict]:
    """Every distinct trip of one direction, fetching only trips not yet seen.

    Walking the stops in order catches trips that start mid-route too: their first
    departure shows up on a later stop with no known trip covering it.
    """
    trips: list[dict] = []
    covered: set[tuple[str, str, int]] = set()   # (label, stop_id, minutes)
    for seq, _name in stops:
        page = site.html(f"rozklad-{edition}-{seq}-{direction}.html")
        current = page.select_one('.current-stop a[href^="przystanek-"]')
        stop_id = current["href"].removeprefix("przystanek-").removesuffix(".html") if current else None
        label = ""
        for el in page.select("#departures .day_type, #departures .one a[onclick]"):
            if "day_type" in (el.get("class") or []):
                label = " ".join(el.get_text(" ", strip=True).split())
                continue
            m_t = TIME_RX.match(el.get_text(strip=True))
            m_k = KURS_RX.search(el.get("onclick", ""))
            if not m_t or not m_k:
                continue
            minutes = int(m_t.group(1)) * 60 + int(m_t.group(2))
            if stop_id and (label, stop_id, minutes) in covered:
                continue
            kat, kier, nr, kurs = m_k.groups()
            trip_label, rows = parse_trip(site.html("kurs.php", {"kat": kat, "kier": kier, "nr": nr, "kurs": kurs, "a": 1}, xhr=True))
            if len(rows) < 2:
                continue
            trip_label = trip_label or label
            trips.append({"label": trip_label, "direction": direction, "stops": rows})
            for sid, _n, mins in rows:
                covered.add((trip_label, sid, mins % (24 * 60)))
            if stop_id:
                covered.add((label, stop_id, minutes))
    return trips


def stop_coordinates(site: Site, edition: str) -> dict[str, tuple[float, float]]:
    """Map markers are posts (one per side of the road); a stop is their centroid.

    Keyed by stop id (id_p, the number in przystanek-<id>.html), and also by name: a stop
    can be renumbered in the timetables before the map catches up (Wodzisław's Targowa
    bus station is 452 in the trips and 37 on the map, October 2026)."""
    page = site.html(f"mapa.html?kat_route={edition}")
    m = re.search(r"var markers_json = (\{.*?\});", str(page), re.S)
    if not m:
        return {}
    acc: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for mk in json.loads(m.group(1)).values():
        try:
            acc[str(mk["id_p"])].append((float(mk["lat"]), float(mk["lng"])))
        except (KeyError, ValueError):
            continue
    by_name: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for mk in json.loads(m.group(1)).values():
        try:
            by_name["name:" + mk["name"]].append((float(mk["lat"]), float(mk["lng"])))
        except (KeyError, ValueError):
            continue
    acc.update(by_name)
    return {k: (round(sum(a for a, _ in v) / len(v), 6), round(sum(b for _, b in v) / len(v), 6)) for k, v in acc.items()}


LOWER = {"i", "w", "z", "na", "do", "od", "pod", "przy", "nad", "ul.", "al.", "os.", "pl."}
ROMAN_RX = re.compile(r"^[IVXLC]+(-[A-ZĄĆĘŁŃÓŚŹŻ]+)?$")


def pretty(name: str) -> str:
    """'SYRYNIA, POWSTAŃCÓW ŚLĄSKICH SZKOŁA' → 'Syrynia, Powstańców Śląskich Szkoła'.
    Roman numerals stay upper ('XXX-lecia'), short connectives stay lower."""
    words = []
    for i, w in enumerate(name.split(" ")):
        if ROMAN_RX.match(w):
            head, _, tail = w.partition("-")
            words.append(head + ("-" + tail.lower() if tail else ""))
        elif i and w.lower() in LOWER:
            words.append(w.lower())
        else:
            words.append("-".join(p[:1].upper() + p[1:].lower() for p in w.split("-")))
    return " ".join(words)


def hhmmss(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}:00"


def csv_bytes(header: list[str], rows: list[list]) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    return buf.getvalue().encode("utf-8")


def build_zip(files: dict[str, bytes]) -> bytes:
    """Fixed timestamps and order: same content, same bytes, same sha256."""
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, files[name])
    return out.getvalue()


def fetch(params: dict, ctx: Ctx) -> dict:
    failures: list[dict] = []
    site = Site(params["base"], params.get("extraCa", []))
    via = re.compile(params["linesVia"], re.IGNORECASE)
    cache_path = ctx.data_dir / "transit_source.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}

    index = lines_index(site)
    log(f"[info] {len(index)} linii w serwisie")

    lines: dict[str, dict] = {}
    elsewhere: list[str] = [e for e in cache.get("elsewhere", []) if e in index]
    for edition, meta in sorted(index.items()):
        cached = cache.get("lines", {}).get(edition)
        if cached:
            lines[edition] = cached
            continue
        if edition in elsewhere:
            continue  # a line known not to touch this gmina, in this same edition
        try:
            dirs = line_stops(site, edition)
            if not any(via.search(name) for stops in dirs.values() for _s, name in stops):
                elsewhere.append(edition)
                continue
            trips: list[dict] = []
            for direction, stops in sorted(dirs.items()):
                trips += collect_trips(site, edition, direction, stops)
            lines[edition] = {**meta, "trips": trips}
            log(f"[info] linia {meta['line']} ({edition}): {len(trips)} kursów, {site.requests} zapytań")
        except Exception as e:  # noqa: BLE001 — one line must not sink the feed
            log(f"[error] linia {meta['line']}: {e}")
            failures.append({"source": f"linia {meta['line']}", "error": str(e)})
            if cached:
                lines[edition] = cached

    if not lines:
        raise RuntimeError("no line passes through the configured places")

    coords = cache.get("coords") if set(cache.get("lines", {})) == set(lines) and cache.get("coordsVersion") == 2 else None
    if not coords:
        coords = stop_coordinates(site, sorted(lines)[0])
    cache = {"generated_at": now_iso(), "lines": lines, "elsewhere": sorted(set(elsewhere)),
             "coords": coords, "coordsVersion": 2}
    # Compact: this is a cache, not something to read, and it changes only with an edition.
    cache_path.write_text(json.dumps(cache, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")

    # ------------------------------------------------------------------ calendar
    school = cal.SchoolCalendar(params["calendar"])
    start = ctx.today.replace(day=1)
    end = min(start + timedelta(days=int(params.get("horizonDays", 150))), school.known_until)
    if end <= ctx.today:
        raise RuntimeError(f"school calendar ends {school.known_until}: add the next school year to sources.json")

    # ------------------------------------------------------------------ GTFS rows
    stops: dict[str, str] = {}
    routes, trips_rows, times_rows = [], [], []
    services: set[str] = set()
    unknown_labels: set[str] = set()
    for edition in sorted(lines):
        ln = lines[edition]
        route_id = ln["line"]
        routes.append([route_id, "1", ln["line"], pretty(ln["name"]) if ln["name"] else "", "3"])
        for n, trip in enumerate(ln["trips"], 1):
            service = cal.day_type(trip["label"])
            if service is None:
                unknown_labels.add(trip["label"])
                continue
            services.add(service)
            trip_id = f"{route_id}-{trip['direction']}-{n}"
            rows = trip["stops"]
            trips_rows.append([route_id, service, trip_id, pretty(rows[-1][1]), str(trip["direction"] - 1)])
            for seq, (sid, name, minutes) in enumerate(rows, 1):
                stops[sid] = name
                times_rows.append([trip_id, hhmmss(minutes), hhmmss(minutes), sid, str(seq)])
    for label in sorted(unknown_labels):
        failures.append({"source": "kalendarz", "error": f"nieznany typ dnia: {label!r}"})
        log(f"[warn] pominięto kursy o typie dnia {label!r}")

    for sid, name in stops.items():
        if sid not in coords and "name:" + name in coords:
            coords[sid] = coords["name:" + name]
    missing = [sid for sid in stops if sid not in coords]
    if missing:
        log(f"[warn] {len(missing)} przystanków bez współrzędnych: {missing[:5]}")
    stops_rows = [[sid, pretty(name), *(f"{c:.6f}" for c in coords.get(sid, (0.0, 0.0)))] for sid, name in sorted(stops.items(), key=lambda kv: int(kv[0]) if kv[0].isdigit() else kv[0])]

    dates_rows = []
    for service in sorted(services):
        for d in cal.service_dates(service, start, end, school):
            dates_rows.append([service, d.strftime("%Y%m%d"), "1"])

    files = {
        "agency.txt": csv_bytes(["agency_id", "agency_name", "agency_url", "agency_timezone", "agency_lang"],
                                [["1", params.get("agency", "Komunikacja powiatowa"), site.base, "Europe/Warsaw", "pl"]]),
        "stops.txt": csv_bytes(["stop_id", "stop_name", "stop_lat", "stop_lon"], stops_rows),
        "routes.txt": csv_bytes(["route_id", "agency_id", "route_short_name", "route_long_name", "route_type"], routes),
        "trips.txt": csv_bytes(["route_id", "service_id", "trip_id", "trip_headsign", "direction_id"], trips_rows),
        "stop_times.txt": csv_bytes(["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"], times_rows),
        "calendar_dates.txt": csv_bytes(["service_id", "date", "exception_type"], dates_rows),
        "feed_info.txt": csv_bytes(["feed_publisher_name", "feed_publisher_url", "feed_lang", "feed_start_date", "feed_end_date", "feed_version"],
                                   [["miasto-engine", "https://github.com/esm0x/miasto-engine", "pl",
                                     start.strftime("%Y%m%d"), end.strftime("%Y%m%d"), "+".join(sorted(lines))]]),
    }
    blob = build_zip(files)
    (ctx.data_dir / "gtfs.zip").write_bytes(blob)

    report = defaultdict(int)
    for row in trips_rows:
        report[(row[0], row[4], row[1])] += 1
    for (route, direction, service), n in sorted(report.items()):
        log(f"[info]   linia {route} kier. {int(direction) + 1} {service:<16} {n:>3} kursów")
    log(f"[info] GTFS: {len(stops_rows)} przystanków, {len(routes)} linii, {len(trips_rows)} kursów, "
        f"{start}…{end}, {len(blob)} B, zapytań: {site.requests}")

    return {
        "generated_at": now_iso(),
        "gtfs_url": ctx.city["dataBaseUrl"] + "gtfs.zip",
        "attachment_id": None,
        "valid_from": start.isoformat(),
        "valid_to": end.isoformat(),
        "stop_count": len(stops_rows),
        "route_count": len(routes),
        "sha256": hashlib.sha256(blob).hexdigest(),
        "editions": sorted(lines),
        "failures": failures,
    }
