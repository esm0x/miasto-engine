"""A source refused by its server, and the second way to the same news."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from engine.common import Ctx
from modules import news
from modules.news import NewsItem
from sources.news import google_news

GOOGLE_RSS = """<?xml version="1.0"?><rss><channel>
<item><title>Brutalny napad w centrum Rybnika - Rybnik.com.pl</title>
  <link>https://news.google.com/rss/articles/CBMi1</link>
  <pubDate>Mon, 12 Oct 2026 09:30:00 GMT</pubDate><source url="https://www.rybnik.com.pl">Rybnik.com.pl</source></item>
<item><title>Portal informacyjny miasta Rybnik - Rybnik.com.pl</title>
  <link>https://news.google.com/rss/articles/CBMi2</link>
  <pubDate>Mon, 12 Oct 2026 17:00:00 GMT</pubDate><source url="https://www.rybnik.com.pl">Rybnik.com.pl</source></item>
<item><title>Artykuły dla tagu wyłączenia wody - Rybnik.com.pl</title>
  <link>https://news.google.com/rss/articles/CBMi3</link>
  <pubDate>Mon, 12 Oct 2026 15:00:00 GMT</pubDate><source url="https://www.rybnik.com.pl">Rybnik.com.pl</source></item>
<item><title>Z głębokim żalem zawiadamiamy, że dnia 10.10.2026 zmarł - Rybnik.com.pl</title>
  <link>https://news.google.com/rss/articles/CBMi5</link>
  <pubDate>Mon, 12 Oct 2026 13:58:00 GMT</pubDate><source url="https://www.rybnik.com.pl">Rybnik.com.pl</source></item>
<item><title>Awaria wodociągu na Rudzkiej - Rybnik.com.pl</title>
  <link>https://news.google.com/rss/articles/CBMi4</link>
  <pubDate>Mon, 12 Oct 2026 08:00:00 GMT</pubDate><source url="https://www.rybnik.com.pl">Rybnik.com.pl</source></item>
</channel></rss>""".encode("utf-8")


class GoogleNews(unittest.TestCase):

    def test_articles_kept_listing_pages_dropped_suffix_cut(self):
        with mock.patch.object(google_news, "get", return_value=mock.Mock(content=GOOGLE_RSS)):
            items = google_news.fetch({"name": "rybnik.com.pl", "site": "rybnik.com.pl"}, None, [])
        self.assertEqual(["Brutalny napad w centrum Rybnika", "Awaria wodociągu na Rudzkiej"],
                         [i.title for i in items])
        self.assertTrue(all(i.source == "rybnik.com.pl" for i in items))
        self.assertEqual("ALERT", items[1].priority)


class Fallback(unittest.TestCase):

    def _run(self, primary, fallback):
        modules = {"rss": mock.Mock(fetch=primary), "google_news": mock.Mock(fetch=fallback)}
        ctx = Ctx(slug="testcity", city={"name": "T"}, sources={"news": {"sources": [
            {"type": "rss", "name": "rybnik.com.pl", "url": "https://x",
             "fallback": {"type": "google_news", "site": "rybnik.com.pl"}}]}})
        with tempfile.TemporaryDirectory() as tmp, \
             mock.patch.object(news, "load_source", side_effect=lambda m, t: modules[t]), \
             mock.patch.object(news, "write_json"), \
             mock.patch.object(news.time, "sleep"), \
             mock.patch.object(Ctx, "data_dir", new_callable=mock.PropertyMock, return_value=Path(tmp)):
            return news.run(ctx)

    def item(self):
        return NewsItem(id="a", title="T", summary="", link="https://news.google.com/a",
                        published="2026-10-12T09:30", source="rybnik.com.pl", category="W", priority="NORMAL")

    def test_403_then_fallback_is_degraded_not_failed(self):
        payload = self._run(mock.Mock(side_effect=RuntimeError("403 Forbidden")), mock.Mock(return_value=[self.item()]))
        self.assertEqual([], payload["failures"])
        self.assertEqual("google_news", payload["degraded"][0]["via"])
        self.assertEqual(1, payload["count"])

    def test_both_down_is_a_failure(self):
        payload = self._run(mock.Mock(side_effect=RuntimeError("403")), mock.Mock(side_effect=RuntimeError("429")))
        self.assertEqual("rybnik.com.pl", payload["failures"][0]["source"])
        self.assertNotIn("degraded", payload)

    def test_fallback_untouched_when_primary_works(self):
        fb = mock.Mock(return_value=[self.item()])
        payload = self._run(mock.Mock(return_value=[self.item()]), fb)
        fb.assert_not_called()
        self.assertNotIn("degraded", payload)


if __name__ == "__main__":
    unittest.main()
