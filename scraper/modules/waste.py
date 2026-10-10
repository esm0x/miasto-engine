"""Waste collection schedules → data/<slug>/waste.json

    "waste": {"sources": [{"type": "rybnik_eu_pdf", "indexUrl": "...", "year": 2026}]}

Every gmina publishes its schedule differently, so this is the module where a new city
costs real work: usually one parser in sources/waste/. Whatever the source, it returns
rejony in the contract's shape; a village listed as a whole gets one street named "*".

Schedules change once a year, so CI runs this only on a manual dispatch or when the
scraper code changes, never on the six-hourly cron.
"""

from __future__ import annotations

from engine.common import Ctx, load_source, log, now_iso, write_json
from engine.contract import check_waste


def run(ctx: Ctx) -> dict:
    cfg = ctx.module("waste") or {}
    rejony: list[dict] = []
    failures: list[dict] = []
    year = None
    for spec in cfg.get("sources", []):
        name = spec.get("name") or spec["type"]
        try:
            got, year = load_source("waste", spec["type"]).fetch(spec, ctx, failures)
            rejony.extend(got)
        except Exception as e:  # noqa: BLE001 — partial data beats no data
            log(f"[error] {name}: {e}")
            failures.append({"source": name, "error": str(e)})

    if not rejony:
        # A schedule never shrinks to nothing mid-year: an empty result is a broken
        # parser or a dead page, and publishing it would wipe every user's calendar.
        raise RuntimeError(f"waste: no rejony parsed ({failures}); keeping the previous file")

    payload = {
        "generated_at": now_iso(),
        "year": year,
        "count": len(rejony),
        "failures": failures,
        "rejony": rejony,
    }
    check_waste(payload)
    out = ctx.data_dir / "waste.json"
    write_json(out, payload)
    log(f"[info] wrote {len(rejony)} rejony (failures: {len(failures)}) → {out}")
    return payload
