#!/usr/bin/env python3
"""Source health: state across runs, STATUS.md, and GitHub issues when a source stays down.

Each city's build writes data/_health/<slug>.json (see build.py). CI's commit job then
runs this once for all cities:

    python scraper/health.py              # update data/_status/state.json and STATUS.md
    python scraper/health.py --issues     # …and open / close GitHub issues

Why issues: with two cities there are some twenty sources, each breaking a few times a
year, and a red run in the Actions tab is something nobody looks at. An issue is
mailed to the repo owner and stays open until the source works again.

What counts as down, per city / module / source:
  * the module failed outright (exception, contract violation; nothing was written);
  * a source raised and was recorded in the payload's `failures`;
  * the module produced zero items where the last good run had some (a layout change
    that parses into nothing raises no error at all);
  * the city sent no report this run (its job died before writing one).
One bad run is noise (a timeout, a 503); an issue opens on the second in a row.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine.common import DATA_DIR, ROOT, all_slugs, utf8_streams  # noqa: E402

HEALTH_DIR = DATA_DIR / "_health"
STATE_PATH = DATA_DIR / "_status" / "state.json"
STATUS_MD = ROOT / "STATUS.md"

THRESHOLD = 2            # consecutive bad runs before an issue opens
STALE_AFTER = timedelta(hours=3)
LABEL = "zrodlo-nie-dziala"
TITLE_PREFIX = "[dane]"

MODULE_NAMES = {
    "events": "Wydarzenia", "news": "Wiadomości", "sport": "Sport",
    "points": "Punkty odpadów", "transit": "Transport", "waste": "Odpady", "river": "Rzeka",
    "gazette": "Gazeta", "places": "Godziny otwarcia",
}


def key(city: str, module: str, source: str) -> str:
    return f"{city}/{module}/{source}"


def problems_in(report: dict[str, Any], previous_counts: dict[str, int]) -> tuple[dict[str, str], dict[str, int]]:
    """This run's problems for one city, keyed module/source → message, and module totals."""
    found: dict[str, str] = {}
    totals: dict[str, int] = {}
    for module, m in report.get("modules", {}).items():
        if m.get("status") != "ok":
            found[f"{module}/*"] = m.get("error") or "moduł nie zadziałał"
            continue
        for f in m.get("failures", []):
            found[f"{module}/{f.get('source', '?')}"] = str(f.get("error", ""))[:300]
        total = int(m.get("total", 0))
        totals[module] = total
        if total == 0 and previous_counts.get(module, 0) > 0:
            found[f"{module}/(pusto)"] = f"0 pozycji, wcześniej {previous_counts[module]}"
    return found, totals


def update(state: dict[str, Any], reports: dict[str, dict], now: datetime, expected: list[str]) -> dict[str, Any]:
    """Pure: the new state from the old one and this run's reports."""
    entries: dict[str, dict] = state.setdefault("entries", {})
    modules: dict[str, dict] = state.setdefault("modules", {})
    current: dict[str, str] = {}

    for city in expected:
        report = reports.get(city)
        fresh = report and datetime.fromisoformat(report["run_at"]) >= now - STALE_AFTER
        if not fresh:
            current[key(city, "*", "raport")] = "miasto nie przysłało raportu w tym przebiegu (zadanie CI padło?)"
            continue
        prev_counts = {m: v.get("last_count", 0) for m, v in modules.get(city, {}).items()}
        found, totals = problems_in(report, prev_counts)
        for k, msg in found.items():
            current[f"{city}/{k}"] = msg
        city_mods = modules.setdefault(city, {})
        for module, m in report.get("modules", {}).items():
            row = city_mods.setdefault(module, {})
            row["last_status"] = m.get("status")
            row["last_run"] = report["run_at"]
            if m.get("status") == "ok":
                row["last_ok"] = report["run_at"]
                # An empty run must not become the new normal, or the second empty run
                # would compare 0 with 0 and a dead parser would never raise an alarm.
                if totals.get(module, 0) > 0 or not row.get("last_count"):
                    row["last_count"] = totals.get(module, 0)
                row["counts"] = m.get("counts", {})
                row["failing_sources"] = [f.get("source") for f in m.get("failures", [])]
            else:
                row["error"] = m.get("error")

    # Only keys whose module ran this time may recover: waste skipped by the cron is
    # not "fixed" just because it did not run.
    ran = {(c, mod) for c, r in reports.items() for mod in r.get("modules", {})}
    for k, entry in list(entries.items()):
        city, module, _ = k.split("/", 2)
        if k in current:
            continue
        if module == "*" and city in reports or (city, module) in ran:
            entry["consecutive"] = 0
            entry["recovered_at"] = now.isoformat(timespec="seconds")
    for k, msg in current.items():
        entry = entries.setdefault(k, {"consecutive": 0})
        if entry.get("consecutive", 0) == 0:
            entry["first_failed"] = now.isoformat(timespec="seconds")
            entry.pop("recovered_at", None)
        entry["consecutive"] = entry.get("consecutive", 0) + 1
        entry["last_error"] = msg
    # Forget entries healthy for a week, so the file does not grow forever.
    for k, entry in list(entries.items()):
        rec = entry.get("recovered_at")
        if entry.get("consecutive", 0) == 0 and rec and datetime.fromisoformat(rec) < now - timedelta(days=7):
            del entries[k]
    state["updated_at"] = now.isoformat(timespec="seconds")
    return state


def safe_text(s: Any, limit: int = 500) -> str:
    """Error text is partly written by the sites we scrape. In an issue or STATUS.md it
    must stay text: no closing the code fence, no links, no @mentions, one line."""
    s = " ".join(str(s).split())[:limit]
    for a, b in (("`", "ʼ"), ("@", "＠"), ("[", "("), ("]", ")"), ("<", "‹"), (">", "›"), ("|", "¦")):
        s = s.replace(a, b)
    return s


def issue_title(k: str) -> str:
    city, module, source = k.split("/", 2)
    return f"{TITLE_PREFIX} {city} / {MODULE_NAMES.get(module, module)} / {safe_text(source, 120)}"


def wanted_issues(state: dict[str, Any]) -> tuple[dict[str, dict], set[str]]:
    """Titles that should be open (with their entry) and titles of recovered sources."""
    open_, closed = {}, set()
    for k, e in state.get("entries", {}).items():
        if e.get("consecutive", 0) >= THRESHOLD:
            open_[issue_title(k)] = e
        elif e.get("consecutive", 0) == 0:
            closed.add(issue_title(k))
    return open_, closed


def render_status(state: dict[str, Any]) -> str:
    lines = [
        "# Status danych",
        "",
        f"Aktualizacja: {state.get('updated_at', '?')} (czas UTC runnera CI). Generowane przez "
        "`scraper/health.py` po każdym przebiegu; nie edytuj ręcznie.",
        "",
        f"Zgłoszenie na GitHubie otwiera się, gdy źródło zawiedzie {THRESHOLD} przebiegi z rzędu, "
        "i zamyka samo, gdy wróci.",
        "",
    ]
    entries = state.get("entries", {})
    # A city that never reported has no module rows yet, and is exactly the one to show.
    cities = set(state.get("modules", {})) | {k.split("/", 1)[0] for k in entries}
    for city in sorted(cities):
        mods = state.get("modules", {}).get(city, {})
        lines += [f"## {city}", "", "| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |", "|---|---|---|---|---|"]
        for module, row in sorted(mods.items()):
            bad = [e for k, e in entries.items() if k.startswith(f"{city}/{module}/") and e.get("consecutive", 0) > 0]
            down = any(e["consecutive"] >= THRESHOLD for e in bad)
            icon = "❌" if row.get("last_status") != "ok" or down else ("⚠️" if bad else "✅")
            counts = ", ".join(f"{s} ({n})" for s, n in sorted(row.get("counts", {}).items()))
            lines.append(f"| {MODULE_NAMES.get(module, module)} | {icon} | {row.get('last_ok', '—')[:16].replace('T', ' ')} "
                         f"| {row.get('last_count', '—')} | {counts} |")
        problems = [(k, e) for k, e in sorted(entries.items()) if k.startswith(f"{city}/") and e.get("consecutive", 0) > 0]
        if problems:
            lines += ["", "Problemy:", ""]
            for k, e in problems:
                lines.append(f"- `{safe_text(k.split('/', 1)[1], 120)}` — {e['consecutive']}× z rzędu od {e.get('first_failed', '?')[:16]}: "
                             f"{safe_text(e.get('last_error', ''), 160)}")
        lines.append("")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- GitHub
def gh(method: str, path: str, body: dict | None = None) -> Any:
    repo, token = os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"]
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}{path}", method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read() or b"null")


def sync_issues(state: dict[str, Any]) -> None:
    want_open, recovered = wanted_issues(state)
    owner = os.environ.get("GITHUB_REPOSITORY_OWNER", "")
    run_url = f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/{os.environ['GITHUB_REPOSITORY']}" \
              f"/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}"
    try:
        gh("POST", "/labels", {"name": LABEL, "color": "d73a4a", "description": "Źródło danych nie działa"})
    except Exception:  # noqa: BLE001 — already exists
        pass
    existing = {i["title"]: i for i in gh("GET", f"/issues?state=open&labels={LABEL}&per_page=100")}
    for title, e in want_open.items():
        if title in existing:
            continue
        body = (f"@{owner} źródło nie działa od **{e['consecutive']}** przebiegów z rzędu "
                f"(od {e.get('first_failed', '?')}).\n\n**Ostatni błąd:**\n```\n{safe_text(e.get('last_error', ''))}\n```\n\n"
                f"Przebieg: {run_url}\nStan wszystkich źródeł: `STATUS.md`.\n\n"
                "Zgłoszenie zamknie się samo, gdy źródło znów zadziała.")
        gh("POST", "/issues", {"title": title, "body": body, "labels": [LABEL]})
        print(f"[issue] opened: {title}")
    for title, issue in existing.items():
        if title in recovered or (title not in want_open and title.startswith(TITLE_PREFIX)):
            gh("POST", f"/issues/{issue['number']}/comments", {"body": f"Źródło znów działa ({run_url}). Zamykam."})
            gh("PATCH", f"/issues/{issue['number']}", {"state": "closed"})
            print(f"[issue] closed: {title}")


def main() -> int:
    utf8_streams()
    p = argparse.ArgumentParser()
    p.add_argument("--issues", action="store_true", help="open/close GitHub issues (needs GITHUB_TOKEN)")
    args = p.parse_args()

    state = json.loads(STATE_PATH.read_text(encoding="utf-8")) if STATE_PATH.exists() else {}
    reports = {}
    for f in HEALTH_DIR.glob("*.json"):
        try:
            r = json.loads(f.read_text(encoding="utf-8"))
            reports[r["slug"]] = r
        except (OSError, ValueError, KeyError) as e:
            print(f"[warn] {f.name}: {e}", file=sys.stderr)
    expected = [s for s in all_slugs() if (ROOT / "cities" / s / "sources.json").exists()]
    state = update(state, reports, datetime.now(), expected)

    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    STATUS_MD.write_text(render_status(state), encoding="utf-8")
    down = [k for k, e in state.get("entries", {}).items() if e.get("consecutive", 0) >= THRESHOLD]
    print(f"[info] status written; down for {THRESHOLD}+ runs: {down or 'nothing'}")
    if args.issues:
        sync_issues(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
