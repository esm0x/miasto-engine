"""The year change. On 1 January the app either proves itself or fails in public."""

import tempfile
import unittest
from pathlib import Path
from datetime import date
from unittest import mock

from engine.common import Ctx
from modules import waste
from modules.waste import NotPublished


def rejon(rid, dates, district="D"):
    return {"id": rid, "name": rid, "district": district, "houseType": "SINGLE_FAMILY",
            "streets": [{"name": "*", "rules": []}],
            "pickups": [{"type": "ZMIESZANE", "dates": dates}], "weekdayRules": []}


class FakeSource:
    """A source with a schedule per year; a missing year is "not published"."""

    def __init__(self, by_year):
        self.by_year = by_year
        self.asked = []

    def fetch(self, params, ctx, failures, year):
        self.asked.append(year)
        if year not in self.by_year:
            raise NotPublished(str(year))
        return [dict(r, pickups=[dict(p) for p in r["pickups"]]) for r in self.by_year[year]]


def run_on(day, source, _unused=None):
    ctx = Ctx(slug="testcity", city={"name": "T"}, sources={"waste": {"sources": [{"type": "fake"}]}}, today=day)
    # data_dir creates its directory on access; keep the test out of the real data/.
    with tempfile.TemporaryDirectory() as tmp, \
         mock.patch.object(waste, "load_source", return_value=source), \
         mock.patch.object(waste, "write_json") as write, \
         mock.patch.object(Ctx, "data_dir", new_callable=mock.PropertyMock, return_value=Path(tmp)):
        payload = waste.run(ctx)
    return payload, write


class YearChange(unittest.TestCase):

    Y26 = [rejon("a", ["2026-12-01", "2026-12-29"]), rejon("b", ["2026-12-30"])]
    Y27 = [rejon("a", ["2027-01-02", "2027-01-16"]), rejon("c", ["2027-01-05"])]

    def test_before_december_next_year_is_not_even_asked(self):
        src = FakeSource({2026: self.Y26, 2027: self.Y27})
        payload, _ = run_on(date(2026, 11, 20), src, None)
        self.assertEqual([2026], src.asked)
        self.assertNotIn("nextYear", payload)

    def test_in_december_next_years_dates_join_the_same_rejony(self):
        src = FakeSource({2026: self.Y26, 2027: self.Y27})
        payload, _ = run_on(date(2026, 12, 15), src, None)
        by_id = {r["id"]: r for r in payload["rejony"]}
        # December stays, January arrives: the 31 Dec reminder for 2 Jan works.
        self.assertEqual(["2026-12-01", "2026-12-29", "2027-01-02", "2027-01-16"],
                         by_id["a"]["pickups"][0]["dates"])
        self.assertEqual(["2026-12-30"], by_id["b"]["pickups"][0]["dates"])
        # A rejon that only exists next year waits for 1 January.
        self.assertNotIn("c", by_id)
        self.assertEqual(2026, payload["year"])
        self.assertEqual(2027, payload["nextYear"])

    def test_december_without_next_year_is_just_this_year(self):
        src = FakeSource({2026: self.Y26})
        payload, _ = run_on(date(2026, 12, 15), src, None)
        self.assertEqual({"a", "b"}, {r["id"] for r in payload["rejony"]})
        self.assertNotIn("nextYear", payload)
        self.assertEqual([], payload["failures"], "next year missing is not a failure")

    def test_on_1_january_the_new_year_is_the_base(self):
        src = FakeSource({2026: self.Y26, 2027: self.Y27})
        payload, _ = run_on(date(2027, 1, 1), src, None)
        self.assertEqual({"a", "c"}, {r["id"] for r in payload["rejony"]})
        self.assertEqual(2027, payload["year"])

    def test_january_before_the_gmina_publishes_keeps_the_old_file(self):
        src = FakeSource({2026: self.Y26})
        with self.assertRaises(RuntimeError):
            run_on(date(2027, 1, 2), src, None)


if __name__ == "__main__":
    unittest.main()
