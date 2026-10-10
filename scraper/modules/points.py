"""Collection points and the "where do I throw this" guide → data/<slug>/waste_points.json

    "points": {
      "sources": [{"type": "rybnik_eu", "base": "..."}]    # or {"type": "manual"}
      "guide": "waste_guide.json"                             # in cities/<slug>/, optional
    }

The guide is NOT scraped: no city publishes a machine-readable per-item list, so it is a
human-maintained file in the city directory. Most of it carries over between gminas;
what changes is whether there is a GPZON and what the local PSZOK accepts.

Output shape is fixed by scraper/CONTRACT.md (waste_points.json).
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

import requests

from engine.common import UA, Ctx, load_source, log, now_iso, write_json
from engine.contract import check_points

HEADERS = {"User-Agent": UA, "Accept-Language": "pl-PL,pl;q=0.9"}


@dataclass
class Point:
    id: str
    name: str
    kind: str                    # PSZOK | GPZON
    address: str
    district: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    hours: str                   # raw line from the page
    accepted: list[str] = field(default_factory=list)
    note: Optional[str] = None
    url: str = ""


def http_get(url: str) -> requests.Response:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r


def load_guide(path: Path) -> list[dict]:
    """The hand-maintained dictionary. A missing or broken file must not kill the run."""
    if not path.exists():
        print(f"[warn] brak {path.name}, słownik będzie pusty", file=sys.stderr)
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"[error] {path.name}: {e}", file=sys.stderr)
        return []

    entries = []
    for row in raw.get("entries", []):
        item, where = row.get("item"), row.get("where")
        if not item or not where:
            print(f"[warn] pomijam wpis bez item/where: {row}", file=sys.stderr)
            continue
        entries.append({
            "item": item,
            "where": where,
            "note": row.get("note"),
            "keywords": row.get("keywords", []),
        })
    return sorted(entries, key=lambda e: e["item"].lower())


def run(ctx: Ctx) -> dict:
    cfg = ctx.module("points") or {}
    points: list[Point] = []
    failures: list[dict] = []

    for spec in cfg.get("sources", []):
        name = spec.get("name") or spec["type"]
        try:
            points.extend(load_source("points", spec["type"]).fetch(spec, ctx, failures))
        except Exception as e:  # noqa: BLE001
            log(f"[error] {name}: {e}")
            failures.append({"source": name, "error": str(e)})

    for p in points:
        if not p.address:
            log(f"[warn] {p.id} bez adresu")
        if not p.hours:
            log(f"[warn] {p.id} bez godzin otwarcia")
        if not p.accepted:
            log(f"[warn] {p.id} bez listy przyjmowanych odpadów")
        log(f"[info] {p.id}: {p.address} | {p.hours} | {len(p.accepted)} frakcji")

    guide = load_guide(ctx.input_file(cfg["guide"])) if cfg.get("guide") else []
    log(f"[info] słownik 'gdzie wyrzucić': {len(guide)} pozycji")

    payload = {
        "generated_at": now_iso(),
        "count": len(points),
        "failures": failures,
        "points": [asdict(p) for p in points],
        "guide": guide,
    }
    check_points(payload)
    out = ctx.data_dir / "waste_points.json"
    write_json(out, payload)
    log(f"[info] wrote {len(points)} points, {len(guide)} guide entries → {out}")
    return payload
