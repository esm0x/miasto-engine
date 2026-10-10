"""Collection points typed in by hand, from cities/<slug>/points.json.

Params: {"file": "points.json"} (relative to the city directory, optional).

For a gmina with one PSZOK described in prose, a scraper would cost more than the data
is worth and would break on the first redesign. The file mirrors the contract's point
shape; copy `hours` from the gmina's page verbatim, typos included, as the scraped
cities do. `accepted` may be empty when the gmina publishes the list only as an image.
"""

from __future__ import annotations

import json

from engine.common import Ctx, log
from modules.points import Point


def fetch(params: dict, ctx: Ctx, failures: list[dict]) -> list[Point]:
    path = ctx.input_file(params.get("file", "points.json"))
    raw = json.loads(path.read_text(encoding="utf-8"))
    points: list[Point] = []
    for i, row in enumerate(raw.get("points", []), 1):
        try:
            points.append(Point(
                id=row["id"],
                name=row["name"],
                kind=row["kind"],
                address=row["address"],
                district=row.get("district"),
                phone=row.get("phone"),
                email=row.get("email"),
                hours=row.get("hours", ""),
                accepted=list(row.get("accepted", [])),
                note=row.get("note"),
                url=row.get("url", ""),
            ))
        except KeyError as e:
            log(f"[warn] {path.name} #{i}: brak pola {e} — pomijam")
    return points
