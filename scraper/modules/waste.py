"""Waste collection schedules → data/<slug>/waste.json

    "waste": {"sources": [{"type": "rybnik_eu_pdf", "indexUrl": ".../harmonogramy-odbioru-{year}"}]}

Every gmina publishes its schedule differently, so this is the module where a new city
costs real work: usually one parser in sources/waste/. Whatever the source, it returns
rejony in the contract's shape; a village listed as a whole gets one street named "*".

The year is decided here, not in the source. A source is asked for one year and either
returns that year's rejony or raises NotPublished. The policy, the same for every city:

  * The current calendar year is the base. If it is not published, nothing is written
    and last year's file stays: a schedule never shrinks to nothing.
  * From December, next year's schedule is fetched as well when the gmina has put it
    out, and its dates are added to the rejony that exist in both years. That is what
    carries the 31 December reminder for a 2 January pickup, and January in the
    calendar view. Rejony that are new next year are left for 1 January: the address
    picker should not offer a rejon whose 2026 dates do not exist.
  * On 1 January the next year becomes the base by the calendar alone, which is why CI
    runs this module once a day and not only when someone pushes.

Before this, a source simply took "the newest year it could find", and a PDF for
2027 put up in December would have wiped the rest of December from everyone's app.
"""

from __future__ import annotations

from engine.common import Ctx, load_source, log, now_iso, write_json
from engine.contract import check_waste

# From this month on, next year's schedule is looked for and merged in.
LOOKAHEAD_FROM_MONTH = 12


class NotPublished(Exception):
    """The gmina has not published this year's schedule (yet)."""


def collect(cfg: dict, ctx: Ctx, year: int, failures: list[dict], quiet: bool = False) -> list[dict]:
    rejony: list[dict] = []
    for spec in cfg.get("sources", []):
        name = spec.get("name") or spec["type"]
        try:
            rejony.extend(load_source("waste", spec["type"]).fetch(spec, ctx, failures, year))
        except NotPublished as e:
            log(f"[info] {name}: {year} not published yet ({e})")
        except Exception as e:  # noqa: BLE001 — partial data beats no data
            log(f"[error] {name} {year}: {e}")
            if not quiet:
                failures.append({"source": name, "error": f"{year}: {e}"})
    return rejony


def merge_next_year(current: list[dict], nxt: list[dict]) -> int:
    """Add next year's dates to the rejony that exist in both years. Returns how many."""
    ahead = {r["id"]: r for r in nxt}
    merged = 0
    for r in current:
        other = ahead.get(r["id"])
        if not other:
            continue
        by_type = {p["type"]: set(p["dates"]) for p in r.get("pickups", [])}
        for p in other.get("pickups", []):
            by_type.setdefault(p["type"], set()).update(p["dates"])
        r["pickups"] = [{"type": t, "dates": sorted(d)} for t, d in by_type.items()]
        merged += 1
    return merged


def run(ctx: Ctx) -> dict:
    cfg = ctx.module("waste") or {}
    failures: list[dict] = []
    year = ctx.today.year

    rejony = collect(cfg, ctx, year, failures)
    if not rejony:
        # A schedule never shrinks to nothing mid-year: an empty result is a broken
        # parser, a dead page, or January before the gmina published. Publishing it
        # would wipe every user's calendar.
        raise RuntimeError(f"waste: no rejony for {year} ({failures}); keeping the previous file")

    next_year = None
    if ctx.today.month >= LOOKAHEAD_FROM_MONTH:
        # A failure here is not this year's problem, so it is logged and not recorded.
        nxt = collect(cfg, ctx, year + 1, [], quiet=True)
        if nxt:
            n = merge_next_year(rejony, nxt)
            next_year = year + 1
            new = len({r["id"] for r in nxt} - {r["id"] for r in rejony})
            log(f"[info] {year + 1}: dates added to {n} rejony; {new} rejony new in {year + 1} wait for 1 January")

    payload = {
        "generated_at": now_iso(),
        "year": year,
        "count": len(rejony),
        "failures": failures,
        "rejony": rejony,
    }
    if next_year:
        payload["nextYear"] = next_year
    check_waste(payload)
    out = ctx.data_dir / "waste.json"
    write_json(out, payload)
    log(f"[info] wrote {len(rejony)} rejony for {year}{f' + {next_year}' if next_year else ''} "
        f"(failures: {len(failures)}) → {out}")
    return payload
