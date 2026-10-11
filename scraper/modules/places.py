"""Opening hours of the places people go to → data/<slug>/places.json

    "places": {"file": "places.json"}        # in cities/<slug>/

What the app does with it: "Co dziś otwarte", each place with "otwarte do 17:00" or
"zamknięte, otwiera jutro o 7:30", and the town hall with a button to book a visit.

Hours are written by hand. Cities publish them as prose ("od wtorku do piątku w
godzinach od 8:30 do 16:00 oraz w soboty i niedziele…", "w miesiącach letnich"), and a
parser that guesses wrong sends someone to a closed door. What the engine does instead
is watch: every place names the page its hours came from, with a hash of that page's
text as it was when the hours were copied. When the page changes, the place is
reported as a failure, STATUS.md shows it, and after two runs an issue asks someone to
read the page again. The data keeps being published meanwhile: a changed page is more
often a new photo than new hours.

    "watch": {"url": "https://…", "selector": "div.col-lg-9", "sha1": "…"}

To get the sha1 after checking a page: python scraper/build.py --city <slug> --only places
prints the current one for every place whose hash does not match.
"""

from __future__ import annotations

import hashlib
import json
import re
import time

from bs4 import BeautifulSoup

from engine.common import UA, Ctx, get, log, now_iso, write_json
from engine.contract import check_places


def page_hash(url: str, selector: str) -> str:
    soup = BeautifulSoup(get(url, headers={"User-Agent": UA}, retries=2).text, "html.parser")
    node = soup.select_one(selector)
    if node is None:
        raise RuntimeError(f"no {selector!r} on the page")
    # Text only, whitespace folded: markup and image names change without the hours changing.
    text = re.sub(r"\s+", " ", node.get_text(" ", strip=True))
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def run(ctx: Ctx) -> dict:
    cfg = ctx.module("places") or {}
    raw = json.loads(ctx.input_file(cfg.get("file", "places.json")).read_text(encoding="utf-8"))
    failures: list[dict] = []
    places = []
    for p in raw.get("places", []):
        watch = p.pop("watch", None)
        if watch:
            try:
                now = page_hash(watch["url"], watch.get("selector", "body"))
                if now != watch.get("sha1"):
                    log(f"[warn] {p['id']}: strona się zmieniła, sprawdź godziny; nowy sha1 {now}")
                    failures.append({"source": p["id"],
                                     "error": f"strona z godzinami się zmieniła ({watch['url']}); sprawdź i wpisz sha1 {now}"})
            except Exception as e:  # noqa: BLE001 — the hours themselves are still good
                failures.append({"source": p["id"], "error": f"nie da się sprawdzić {watch['url']}: {e}"})
            time.sleep(0.5)
            p.setdefault("sourceUrl", watch["url"])
        places.append(p)
    payload = {"generated_at": now_iso(), "failures": failures, "places": places}
    check_places(payload)
    out = ctx.data_dir / "places.json"
    write_json(out, payload)
    log(f"[info] wrote {len(places)} places (failures: {len(failures)}) → {out}")
    return payload
