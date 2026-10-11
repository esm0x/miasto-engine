"""When an issue opens and closes. Too eager and it is spam; too lazy and a dead
source goes unnoticed for a week."""

import unittest
from datetime import datetime, timedelta

import health

T0 = datetime(2026, 10, 11, 6, 30)


def report(at, **modules):
    return {"slug": "lubomia", "run_at": at.isoformat(timespec="seconds"), "modules": modules}


def ok(total=10, failures=()):
    return {"status": "ok", "total": total, "counts": {"x": total}, "failures": list(failures)}


def failed(error="ContractError: x"):
    return {"status": "failed", "error": error}


def run(state, at, **modules):
    return health.update(state, {"lubomia": report(at, **modules)}, at, ["lubomia"])


class Threshold(unittest.TestCase):

    def test_one_bad_run_is_noise_two_open_an_issue(self):
        s = run({}, T0, news=ok(failures=[{"source": "Radio 90", "error": "503"}]))
        self.assertEqual({}, health.wanted_issues(s)[0])
        s = run(s, T0 + timedelta(hours=6), news=ok(failures=[{"source": "Radio 90", "error": "503"}]))
        self.assertEqual(["[dane] lubomia / Wiadomości / Radio 90"], list(health.wanted_issues(s)[0]))

    def test_recovery_closes_it(self):
        s = run({}, T0, news=ok(failures=[{"source": "Radio 90", "error": "503"}]))
        s = run(s, T0 + timedelta(hours=6), news=ok(failures=[{"source": "Radio 90", "error": "503"}]))
        s = run(s, T0 + timedelta(hours=12), news=ok())
        opened, recovered = health.wanted_issues(s)
        self.assertEqual({}, opened)
        self.assertIn("[dane] lubomia / Wiadomości / Radio 90", recovered)

    def test_a_failed_module_counts(self):
        s = run({}, T0, events=failed())
        s = run(s, T0 + timedelta(hours=6), events=failed())
        self.assertIn("[dane] lubomia / Wydarzenia / *", health.wanted_issues(s)[0])

    def test_silent_emptiness_counts(self):
        """A layout change parses into nothing and raises nothing."""
        s = run({}, T0, events=ok(total=20))
        s = run(s, T0 + timedelta(hours=6), events=ok(total=0))
        s = run(s, T0 + timedelta(hours=12), events=ok(total=0))
        self.assertIn("[dane] lubomia / Wydarzenia / (pusto)", health.wanted_issues(s)[0])

    def test_a_city_that_did_not_report(self):
        s = run({}, T0, news=ok())
        later = T0 + timedelta(hours=12)
        s = health.update(s, {"lubomia": report(T0, news=ok())}, later, ["lubomia"])  # stale report
        s = health.update(s, {}, later + timedelta(hours=6), ["lubomia"])             # none at all
        self.assertIn("[dane] lubomia / * / raport", health.wanted_issues(s)[0])

    def test_a_module_that_did_not_run_does_not_recover(self):
        """The cron skips waste; that must not close a waste issue."""
        s = run({}, T0, waste=failed())
        s = run(s, T0 + timedelta(hours=6), waste=failed())
        s = run(s, T0 + timedelta(hours=12), news=ok())
        self.assertIn("[dane] lubomia / Odpady / *", health.wanted_issues(s)[0])

    def test_status_page_names_the_problem(self):
        s = run({}, T0, news=ok(failures=[{"source": "Radio 90", "error": "HTTP 503"}]), events=ok(total=5))
        md = health.render_status(s)
        self.assertIn("## lubomia", md)
        self.assertIn("Radio 90", md)
        self.assertIn("HTTP 503", md)


if __name__ == "__main__":
    unittest.main()
