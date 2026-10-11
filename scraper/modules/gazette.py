"""The city's own newspaper, issue by issue → data/<slug>/gazette.json

    "gazette": {"title": "Kurier Żorski",
                "sources": [{"type": "typo3_figures",
                             "pages": ["https://www.zory.pl/", ".../aktualne-wydanie"],
                             "hosts": ["zory.pl"]}],
                "maxIssues": 24}

A gazette is a PDF per issue on the city's site. The app lists the issues and opens
the PDF in the browser; a new issue at the top of the list is what its notification
says. Nothing is downloaded here but the pages that link the PDFs.
"""

from __future__ import annotations

from engine.common import Ctx, load_source, log, now_iso, write_json
from engine.contract import check_gazette


def run(ctx: Ctx) -> dict:
    cfg = ctx.module("gazette") or {}
    failures: list[dict] = []
    issues: dict[str, dict] = {}
    for spec in cfg.get("sources", []):
        name = spec.get("name") or spec["type"]
        try:
            for issue in load_source("gazette", spec["type"]).fetch(spec, ctx, failures):
                # The same issue is linked from several pages; the first page listed wins.
                issues.setdefault(issue["id"], issue)
        except Exception as e:  # noqa: BLE001
            log(f"[error] {name}: {e}")
            failures.append({"source": name, "error": str(e)})
    if not issues:
        raise RuntimeError(f"gazette: no issues found ({failures}); keeping the previous file")
    ordered = sorted(issues.values(), key=lambda i: (i["year"], i["number"]), reverse=True)
    payload = {
        "generated_at": now_iso(),
        "title": cfg.get("title") or ctx.name,
        "failures": failures,
        "issues": ordered[: int(cfg.get("maxIssues", 24))],
    }
    check_gazette(payload)
    out = ctx.data_dir / "gazette.json"
    write_json(out, payload)
    newest = ordered[0]
    log(f"[info] wrote {len(payload['issues'])} issues, newest {newest['label']} → {out}")
    return payload
