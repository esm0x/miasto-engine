"""A schedule PDF with one table per rejon: waste types as rows, twelve months as
columns, days of the month in the cells. Lubomia's layout (operator TRANSGÓR, 2026).

Params:
    {"page": "https://lubomia.pl/cms/6050/odpady",           # where the PDF is linked
     "linkText": "harmonogram wywozu odpadów",              # case-insensitive, with the year
     "pdfUrl": "https://…/harmonogram_lubomia_2026.pdf",    # optional: skip the lookup
     "types": {"Niesegregowane": "ZMIESZANE", "Popi[oó][łl]": "POPIOLY", ...},  # optional
     "pdfHosts": ["lubomia.pl", "idcom-jst.pl"]}           # hosts the PDF may come from

The newest link whose text matches and names a year wins, so next January's schedule
is picked up without a config change once the gmina links it.

Two pitfalls, both from the real 2026 file:
  * The rejon's description (its list of streets) is laid out around the "Rejon II"
    label: part of it lands in the text line BEFORE the label, part AFTER. Reading by
    lines loses the streets of rejony II and III. The tables bind label and description
    correctly, so this reads tables and uses text only for the operator name.
  * A rejon covers several villages ("Buków, Grabówka, Nieboczowy, Syrynia: Dąbrowy"),
    while the app's address model has one district per rejon. Each village becomes its
    own rejon entry with the same pickups; a village named without streets gets "*".
"""

from __future__ import annotations

import io
import re
from datetime import date
from typing import Optional
from urllib.parse import urljoin, urlsplit

import pdfplumber
from bs4 import BeautifulSoup

from engine.common import UA, Ctx, get, log, same_site, slug

ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6,
         "VII": 7, "VIII": 8, "IX": 9, "X": 10, "XI": 11, "XII": 12}

# Row label in the PDF → contract enum. Matched as a regex against the first cell.
# Order matters: "Niesegregowane" also contains "segregowane".
DEFAULT_TYPES = {
    r"Niesegregowane": "ZMIESZANE",
    r"Popi[oó][łl]": "POPIOLY",
    r"Odpady segregowane": "SEGREGOWANE",
    r"biodegradacj": "BIO",
    r"wielkogabarytow": "GABARYTY",
}


def find_pdf(page_url: str, link_text: str, hosts: list[str]) -> tuple[str, int]:
    """The newest '<link_text> … <year>' link on the page, with its year."""
    html = get(page_url, headers={"User-Agent": UA}, retries=2).text
    soup = BeautifulSoup(html, "html.parser")
    best: Optional[tuple[int, str]] = None
    for a in soup.select("a[href]"):
        text = " ".join(a.get_text(" ", strip=True).split())
        href = a["href"]
        if link_text.lower() not in text.lower() or not href.lower().split("?")[0].endswith(".pdf"):
            continue
        years = re.findall(r"20\d\d", f"{text} {href}")
        if not years:
            continue
        year = max(int(y) for y in years)
        if best is None or year > best[0]:
            best = (year, urljoin(page_url, href))
    if best is not None and not same_site(best[1], *hosts):
        raise RuntimeError(f"schedule link {best[1]} is not on {hosts}; refusing to follow it")
    if best is None:
        raise RuntimeError(f"no '{link_text}' PDF linked on {page_url}")
    return best[1], best[0]


def waste_type(label: str, types: dict[str, str]) -> Optional[str]:
    for pattern, code in types.items():
        if re.search(pattern, label, re.I):
            return code
    return None


def parse_tables(data: bytes, types: dict[str, str]) -> list[dict]:
    regions: list[dict] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                current = None
                for row in table:
                    cells = [(c or "").strip() for c in row]
                    if not " ".join(cells).strip():
                        continue
                    m = re.match(r"Rejon\s+([IVX]+)\b", cells[0] if cells else "")
                    if m:
                        opis = " ".join(c for c in cells[1:] if c)
                        current = {"rejon": m.group(1), "opis": re.sub(r"\s+", " ", opis).strip(),
                                   "odbiory": {}}
                        regions.append(current)
                        continue
                    if current is None or re.match(r"Miesi[ąa]c", cells[0] if cells else ""):
                        continue
                    code = waste_type(cells[0] if cells else "", types)
                    if not code:
                        continue
                    day_cells = [c for c in cells[1:] if c != ""]
                    months: dict[int, list[int]] = {}
                    for i, col in enumerate(day_cells[:12], start=1):
                        if col.strip() == "-":
                            continue
                        days = [int(d) for d in re.findall(r"\d+", col) if 1 <= int(d) <= 31]
                        if days:
                            months[i] = days
                    if months:
                        # Two rows can map to one type (e.g. two kinds of segregated bags
                        # collected together); merge rather than overwrite.
                        merged = current["odbiory"].setdefault(code, {})
                        for mth, days in months.items():
                            merged[mth] = sorted(set(merged.get(mth, [])) | set(days))
    return regions


def split_places(opis: str) -> list[tuple[str, Optional[str]]]:
    """'Syrynia: 3 Maja, Musioła - Lubomia: Potocka' → [(Syrynia, 3 Maja), …];
    'Buków, Grabówka' (no colon) → [(Buków, None), (Grabówka, None)]."""
    opis = re.sub(r"\s+", " ", opis).strip(" ,")
    out: list[tuple[str, Optional[str]]] = []
    parts = re.split(r"\s*-\s*(?=[A-ZŁŚŻŹĆÓĘĄŃ][a-ząćęłńóśźż]+\s*:)", opis)
    for part in parts:
        if ":" in part:
            place, streets = part.split(":", 1)
        else:
            place, streets = part, ""
        place = place.strip(" ,-")
        if streets.strip():
            for s in streets.split(","):
                s = s.strip(" .,")
                if 1 < len(s) < 45:
                    out.append((place, s))
        else:
            for p in place.split(","):
                p = p.strip(" .,")
                if 1 < len(p) < 45:
                    out.append((p, None))
    return out


def tidy_street(name: str) -> str:
    """'3 -Maja' → '3 Maja', '8-Maja' → '8 Maja': the PDF hyphenates dates at random."""
    name = re.sub(r"^(\d+)\s*-\s*", r"\1 ", name)
    return " ".join(name.split())


def to_rejony(regions: list[dict], year: int) -> list[dict]:
    rejony: list[dict] = []
    for r in regions:
        pickups = []
        for code, months in sorted(r["odbiory"].items()):
            dates = []
            for mth, days in months.items():
                for d in days:
                    try:
                        dates.append(date(year, mth, d).isoformat())
                    except ValueError:
                        log(f"[warn] rejon {r['rejon']}: {d}.{mth}.{year} does not exist, skipped")
            pickups.append({"type": code, "dates": sorted(set(dates))})

        by_place: dict[str, list[str]] = {}
        for place, street in split_places(r["opis"]):
            by_place.setdefault(place, [])
            name = tidy_street(street) if street else "*"
            if name not in by_place[place]:
                by_place[place].append(name)

        for place, streets in by_place.items():
            # "*" next to named streets would swallow the village: a place listed both
            # whole and by streets keeps the streets.
            if len(streets) > 1 and "*" in streets:
                streets = [s for s in streets if s != "*"]
            rejony.append({
                "id": f"rejon-{r['rejon'].lower()}-{slug(place)}",
                "name": f"Rejon {r['rejon']}",
                "district": place,
                "houseType": "SINGLE_FAMILY",
                "streets": [{"name": s, "rules": []} for s in sorted(streets)],
                "pickups": pickups,
                "weekdayRules": [],
            })
    return rejony


def fetch(params: dict, ctx: Ctx, failures: list[dict]) -> tuple[list[dict], int]:
    if params.get("pdfUrl"):
        url = params["pdfUrl"]
        years = re.findall(r"20\d\d", url)
        year = int(params.get("year") or max(int(y) for y in years))
    else:
        hosts = params.get("pdfHosts") or [urlsplit(params["page"]).hostname or ""]
        url, year = find_pdf(params["page"], params["linkText"], hosts)
    log(f"[info] harmonogram {year}: {url}")
    data = get(url, headers={"User-Agent": UA}, timeout=60, retries=2).content
    types = params.get("types") or DEFAULT_TYPES
    regions = parse_tables(data, types)
    rejony = to_rejony(regions, year)

    log(f"[info] rejonów w PDF: {len(regions)} → wpisów miejscowość×rejon: {len(rejony)}")
    for r in regions:
        n = sum(len(d) for m in r["odbiory"].values() for d in m.values())
        log(f"[info]   Rejon {r['rejon']:<4} odbiorów: {n:>3}  [{', '.join(sorted(r['odbiory']))}]")
    if not regions:
        failures.append({"source": url, "error": "no 'Rejon' tables found"})
    return rejony, year
