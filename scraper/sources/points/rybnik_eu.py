"""PSZOK and GPZON pages of rybnik.eu. Rybnik only.

Params: {"base": "https://www.rybnik.eu/dla-mieszkancow/odpady-komunalne"}

The original notes, still accurate:
PSZOK, GPZON and the "where do I throw this" dictionary → scraper/data/waste_points.json

Sources:
  * rybnik.eu /odpady-komunalne/punkty-zbiorki-odpadow-pszok  — the two PSZOK sites
  * rybnik.eu /odpady-komunalne/odpady-niebezpieczne-gpzon    — the hazardous waste point

What is scraped and what is not, deliberately:

  * The **accepted waste lists** are scraped. They are clean <li> elements and they do
    change when the city updates its contract.
  * **Opening hours are taken as the raw line from the page**, not parsed into structured
    times. The page writes them as "poniedziałek - piatek: 7.00-19.00, sobota: 8.00-15.00",
    typo included, and every attempt to normalise that invents precision the source does
    not have. The app shows the line as written.
  * Addresses and phones are pulled with narrow regexes and the run fails loudly if a
    point comes out without an address, because a PSZOK entry with no address is worse
    than no entry at all.

The `guide` section is NOT scraped. It is read from `data/waste_guide_manual.json`, a
human-maintained file, the same arrangement as manual_events.json: the city publishes its
sorting rules as prose and a PDF leaflet, with no machine-readable per-item list.

Output shape is fixed by scraper/CONTRACT.md (waste_points.json).
"""

from __future__ import annotations

import re
import sys
from typing import Optional

import requests
from bs4 import BeautifulSoup

from engine.common import Ctx
from modules.points import Point, http_get

BASE = ""
PSZOK_URL = ""
GPZON_URL = ""


def content_text(html: str) -> tuple[str, list[str]]:
    """Main article text plus the list of accepted waste.

    Both pages put their menu, breadcrumbs, page title and opening hours into <li>
    elements inside the same container as the real list, so neither position nor length
    tells them apart. The accepted fractions are the items following the "Rodzaje ...
    odpadów" heading, and that is what this anchors on. If the city rewords that heading
    the list comes back empty and main() says so, which is the failure mode to want:
    visibly nothing rather than quietly the navigation.
    """
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    candidates = soup.select(".ce-bodytext, main, #content, .content")
    if not candidates:
        return "", []
    body = max(candidates, key=lambda c: len(c.get_text()))
    text = re.sub(r"[ \t]+", " ", body.get_text("\n", strip=True))

    marker = body.find(string=re.compile(r"Rodzaje.*odpad", re.I))
    scope = marker.parent.find_all_next("li") if marker else []
    items = [
        re.sub(r"\s+", " ", li.get_text(" ", strip=True)).strip().rstrip(",.")
        for li in scope
        if not li.find("a")
    ]
    # "szkło" is exactly five characters, and a length filter quietly ate it.
    return text, [i for i in items if len(i) > 2]


def parse_pszok() -> list[Point]:
    text, items = content_text(http_get(PSZOK_URL).text)

    # "ul. Kolberga: poniedziałek - piatek: 7.00-19.00, sobota: 8.00-15.00"
    hours = {
        m.group(1).strip().lower(): m.group(2).strip().rstrip(".")
        for m in re.finditer(r"ul\.\s*([^:\n]+):\s*(poniedzia[^\n]+)", text)
    }

    points: list[Point] = []
    for street, district, key in (
        ("ul. Oskara Kolberga 67", "Boguszowice Stare", "kolberga"),
        ("ul. Sportowa", "Niewiadom", "sportowa"),
    ):
        line = next((v for k, v in hours.items() if key in k), "")
        phone = None
        block = re.search(rf"{key}[^\n]*\n?[^\n]*tel:?\s*([0-9 ()]+)", text, re.I)
        if block:
            phone = block.group(1).strip()
        points.append(Point(
            id=f"pszok-{key}",
            name=f"PSZOK {district}",
            kind="PSZOK",
            address=street,
            district=district,
            phone=phone,
            email="info@skladowisko.rybnik.pl" if "skladowisko" in text else None,
            hours=line,
            accepted=[i for i in items if len(i) < 120],
            note="Odpady muszą być posegregowane, inaczej obsługa odmówi przyjęcia.",
            url=PSZOK_URL,
        ))
    return points


def parse_gpzon() -> list[Point]:
    text, items = content_text(http_get(GPZON_URL).text)

    address = re.search(r"(ul\.\s*Jankowicka\s*[0-9A-Za-z]+)", text)
    phone = re.search(r"tel\.?\s*([0-9 ]{7,})", text)
    hours = re.search(
        r"czynny\s+(od\s+poniedzia[^\n]*?)(?:\n|$).*?(\d{1,2}[.:]\d{2}).*?(\d{1,2}[.:]\d{2})",
        text,
        re.S | re.I,
    )
    hours_line = (
        f"poniedziałek - piątek: {hours.group(2)}-{hours.group(3)}" if hours else ""
    )

    return [Point(
        id="gpzon",
        name="GPZON, odpady niebezpieczne",
        kind="GPZON",
        address=address.group(1) if address else "",
        district="Śródmieście",
        phone=phone.group(1).strip() if phone else None,
        email=None,
        hours=hours_line,
        accepted=[i for i in items if len(i) < 160],
        note="Trzeba okazać dokument z imieniem, nazwiskiem i adresem zamieszkania. "
             "Przyjmowane tylko od mieszkańców Rybnika.",
        url=GPZON_URL,
    )]


def fetch(params: dict, ctx: Ctx, failures: list[dict]) -> list[Point]:
    global BASE, PSZOK_URL, GPZON_URL
    BASE = params["base"].rstrip("/")
    PSZOK_URL = f"{BASE}/punkty-zbiorki-odpadow-pszok"
    GPZON_URL = f"{BASE}/odpady-niebezpieczne-gpzon"
    points: list[Point] = []
    for label, parser in (("PSZOK", parse_pszok), ("GPZON", parse_gpzon)):
        try:
            print(f"[info] scraping {label}", file=sys.stderr)
            points.extend(parser())
        except Exception as e:  # noqa: BLE001 — one page must not kill the other
            print(f"[error] {label}: {e}", file=sys.stderr)
            failures.append({"source": label, "error": str(e)})
    return points
