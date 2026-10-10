#!/usr/bin/env python3
"""Build one city's data, or every city's.

    python scraper/build.py --city rybnik                  # all modules the city has
    python scraper/build.py --city lubomia --only news,events
    python scraper/build.py --all --skip waste             # what the cron runs
    python scraper/build.py --list                         # cities and their modules

A city is cities/<slug>/ with city.json (identity, read by the app too) and
sources.json (which parsers feed which module). The modules a city has are the keys of
its sources.json; output lands in data/<slug>/.

Modules are independent: one that fails is reported and the others still run, and the
exit code is non-zero so CI shows it. A module that breaks the contract writes nothing,
so the last good file stays published.
"""

from __future__ import annotations

import argparse
import importlib
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine.common import all_slugs, load_ctx, log, utf8_streams  # noqa: E402

# Order matters only for the log; each module reads its own sources.
MODULES = ["events", "news", "sport", "points", "transit", "waste"]


def build_city(slug: str, only: set[str] | None, skip: set[str]) -> dict[str, str]:
    ctx = load_ctx(slug)
    results: dict[str, str] = {}
    for name in MODULES:
        if name not in ctx.sources:
            continue
        if (only and name not in only) or name in skip:
            continue
        log(f"\n{'#' * 70}\n# {slug} / {name}\n{'#' * 70}")
        started = time.monotonic()
        try:
            importlib.import_module(f"modules.{name}").run(ctx)
            results[name] = f"ok ({time.monotonic() - started:.0f}s)"
        except Exception as e:  # noqa: BLE001 — the next module still runs
            traceback.print_exc()
            results[name] = f"FAILED: {type(e).__name__}: {str(e).splitlines()[0][:160]}"
    return results


def main() -> int:
    utf8_streams()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    target = p.add_mutually_exclusive_group(required=True)
    target.add_argument("--city", action="append", help="city slug; repeatable")
    target.add_argument("--all", action="store_true", help="every city under cities/")
    target.add_argument("--list", action="store_true", help="list cities and their modules")
    p.add_argument("--only", help="comma-separated modules to run")
    p.add_argument("--skip", default="", help="comma-separated modules to skip")
    args = p.parse_args()

    if args.list:
        for slug in all_slugs():
            ctx = load_ctx(slug)
            mods = [m for m in MODULES if m in ctx.sources]
            print(f"{slug:<12} {ctx.city.get('appName', ''):<18} {', '.join(mods) or '(no sources.json)'}")
        return 0

    only = {m.strip() for m in args.only.split(",")} if args.only else None
    skip = {m.strip() for m in args.skip.split(",") if m.strip()}
    slugs = all_slugs() if args.all else args.city

    summary: dict[str, dict[str, str]] = {}
    for slug in slugs:
        summary[slug] = build_city(slug, only, skip)

    log(f"\n{'=' * 70}\nSUMMARY")
    failed = False
    for slug, results in summary.items():
        for module, status in results.items():
            log(f"  {slug:<12} {module:<8} {status}")
            failed |= status.startswith("FAILED")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
