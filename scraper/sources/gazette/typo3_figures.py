"""Gazette issues shown as cover images on TYPO3 pages: <figure><a href=PDF><img></a>
<figcaption>Nr 6, wrzesień 2026</figcaption></figure> (zory.pl, Kurier Żorski).

Params:
    {"pages": ["https://www.zory.pl/", "https://www.zory.pl/czas-wolny/kurier-zorski/aktualne-wydanie"],
     "hosts": ["zory.pl"], "pdfPattern": "kz\\d|kurier"}

pdfPattern keeps other PDFs out: the home page has figures of its own, and one with
"Uchwała nr 12/2026" under it is not an issue. Issue 4 of 2026 sits under
/aktualnosci/, so the pattern looks at the file name, not the folder.

The home page carries the newest issue days before the gazette's own page does, so it
is listed first. Captions are written by hand: "Nr 1 - luty 2026 r.", "Nr 2 marzec
2025 r.", "Nr 5, sierpień 2026". The number comes from "Nr N", the year from the
caption or else the PDF's path (/2026/…); a figure with neither is not an issue.
"""

from __future__ import annotations

import re
import time
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from engine.common import UA, Ctx, clean_text, get, log, same_site

NUMBER = re.compile(r"\bnr\.?\s*(\d{1,2})\b", re.IGNORECASE)
YEAR = re.compile(r"\b(20\d\d)\b")


def issue_from(fig, page: str, hosts: list[str], pattern: re.Pattern) -> Optional[dict]:
    a = fig.find("a", href=True)
    if not a:
        return None
    pdf = urljoin(page, a["href"])
    if not pdf.lower().endswith(".pdf") or not same_site(pdf, *hosts) or not pdf.startswith("https://"):
        return None
    if not pattern.search(pdf.rsplit("/", 1)[-1]):
        return None
    img = fig.find("img")
    cap = fig.find("figcaption")
    label = clean_text(cap.get_text(" ", strip=True) if cap else (img.get("alt") if img else "")) or ""
    number = NUMBER.search(label)
    year = YEAR.search(label) or YEAR.search(pdf)
    if not number or not year:
        return None
    cover = urljoin(page, img["src"]) if img and img.get("src") else None
    if cover and (not same_site(cover, *hosts) or not cover.startswith("https://")):
        cover = None
    n, y = int(number.group(1)), int(year.group(1))
    return {
        "id": f"{y}-{n:02d}",
        "number": n,
        "year": y,
        "label": re.sub(r"\s+r\.?$", "", label).strip(" .,-"),
        "pdfUrl": pdf,
        "coverUrl": cover,
    }


def fetch(params: dict, ctx: Ctx, failures: list[dict]) -> list[dict]:
    hosts = params["hosts"]
    pattern = re.compile(params.get("pdfPattern", "."), re.IGNORECASE)
    out: list[dict] = []
    for page in params["pages"]:
        try:
            soup = BeautifulSoup(get(page, headers={"User-Agent": UA}, retries=2).text, "html.parser")
        except Exception as e:  # noqa: BLE001 — the other pages may still list the issues
            failures.append({"source": page, "error": str(e)})
            continue
        found = [i for f in soup.select("figure") if (i := issue_from(f, page, hosts, pattern))]
        log(f"[info] {page}: {len(found)} numerów")
        out.extend(found)
        time.sleep(0.5)
    return out
