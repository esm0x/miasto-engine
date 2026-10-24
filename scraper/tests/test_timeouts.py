"""A slow server must cost one module, not the city's whole job."""

import signal
import time
import unittest
from unittest import mock

import build
from engine import common
from engine.common import TooSlow


class SlowBody(unittest.TestCase):

    def test_a_dripping_body_is_cut_off(self):
        r = mock.Mock()
        r.headers = {}
        r.raise_for_status = mock.Mock()
        r.encoding = "utf-8"
        r.iter_content = mock.Mock(return_value=iter([b"x"] * 10))
        clock = iter(range(0, 1000, 50))   # each chunk "arrives" 50 s after the last
        with mock.patch.object(common.requests, "get", return_value=r), \
             mock.patch.object(common.time, "monotonic", side_effect=lambda: next(clock)):
            with self.assertRaises(TooSlow):
                common.get("https://zory.pl/x", timeout=30)


@unittest.skipUnless(hasattr(signal, "SIGALRM"), "SIGALRM: Linux CI only")
class ModuleBudget(unittest.TestCase):

    def test_a_stuck_module_fails_alone(self):
        slow = mock.Mock(run=lambda ctx: time.sleep(5))
        fast = mock.Mock(run=lambda ctx: {"failures": [], "items": []})
        ctx = mock.Mock(sources={"events": {}, "news": {}})

        def module(name):
            return slow if name == "modules.events" else fast

        with mock.patch.object(build, "load_ctx", return_value=ctx), \
             mock.patch.object(build.importlib, "import_module", side_effect=module), \
             mock.patch.object(build, "write_json") as write, \
             mock.patch.object(build, "MODULE_BUDGET_S", 1):
            results = build.build_city("zory", None, set())
        self.assertTrue(results["events"].startswith("FAILED: ModuleTimeout"), results)
        self.assertTrue(results["news"].startswith("ok"), results)
        health = write.call_args[0][1]["modules"]
        self.assertEqual("failed", health["events"]["status"])


if __name__ == "__main__":
    unittest.main()
