"""Where this city's GTFS lives → data/<slug>/transit_meta.json

    "transit": {"type": "km_rybnik"}

The timetable is far too big for JSON, so the app downloads gtfs.zip itself. A source
says WHERE the current edition is and proves it is usable; the zip is downloaded for
verification only and never committed. A town whose operator publishes a stable GTFS
URL needs a source of a few lines; one that publishes none has no transit module.
"""

from __future__ import annotations

from engine.common import Ctx, load_source, log, write_json
from engine.contract import check_transit


def run(ctx: Ctx) -> dict:
    cfg = ctx.module("transit") or {}
    payload = load_source("transit", cfg["type"]).fetch(cfg, ctx)
    check_transit(payload)
    out = ctx.data_dir / "transit_meta.json"
    write_json(out, payload)
    log(f"\n[info] wrote transit_meta.json (failures: {len(payload.get('failures', []))}) → {out}")
    return payload
