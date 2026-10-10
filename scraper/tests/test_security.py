"""What a hostile or broken source must not be able to do through the scrapers.

The scrapers read pages nobody here controls and publish the result to every phone.
Each test is one way that could go wrong: a link the app would hand to Android, a
path that walks out of the city directory, a download that never ends.
"""

import unittest
from unittest import mock

from engine import common
from engine.common import Ctx, TooLarge, is_web_url, load_ctx, same_site
from engine.contract import ContractError, check_events, check_news, check_points


def news_payload(link):
    return {"generated_at": "x", "failures": [], "items": [{
        "id": "a", "title": "T", "summary": "", "link": link, "published": "2026-10-10T10:00",
        "source": "s", "category": "c", "priority": "NORMAL"}]}


def events_payload(url):
    return {"generated_at": "x", "failures": [], "events": [{
        "id": "e", "title": "T", "category": "Inne", "start": "2026-10-10T10:00", "end": None,
        "venue": "V", "description": None, "sourceName": "s", "sourceUrl": url}]}


class Links(unittest.TestCase):

    def test_only_web_links_count_as_links(self):
        for bad in ("javascript:alert(1)", "intent://x#Intent;end", "file:///etc/passwd",
                    "content://x", "  ", "", None, "data:text/html,<b>"):
            self.assertFalse(is_web_url(bad), bad)
        for good in ("https://lubomia.pl/x", "http://www.90minut.pl/mecz.php?id_mecz=1", " HTTPS://A.PL "):
            self.assertTrue(is_web_url(good), good)

    def test_contract_rejects_a_news_link_the_app_must_not_open(self):
        with self.assertRaises(ContractError):
            check_news(news_payload("javascript:alert(document.cookie)"))
        check_news(news_payload("https://lubomia.pl/wiadomosci/1/x"))

    def test_contract_allows_an_event_without_a_link_but_not_a_hostile_one(self):
        check_events(events_payload(""))
        with self.assertRaises(ContractError):
            check_events(events_payload("intent://scan/#Intent;scheme=zxing;end"))

    def test_contract_rejects_a_point_link_that_is_not_web(self):
        payload = {"generated_at": "x", "failures": [], "guide": [], "points": [{
            "id": "p", "name": "PSZOK", "kind": "PSZOK", "address": "ul. Szkolna 4", "url": "tel:112"}]}
        with self.assertRaises(ContractError):
            check_points(payload)

    def test_contract_caps_absurd_sizes(self):
        p = news_payload("https://a.pl/1")
        p["items"][0]["summary"] = "x" * 6000
        with self.assertRaises(ContractError):
            check_news(p)


class FollowingLinks(unittest.TestCase):

    def test_same_site_keeps_the_scraper_on_chosen_hosts(self):
        self.assertTrue(same_site("https://lubomia.pl/wiadomosci/1/x", "lubomia.pl"))
        self.assertTrue(same_site("https://cms-v2-files.idcom-jst.pl/sites/158/a.pdf", "idcom-jst.pl"))
        self.assertTrue(same_site("https://www.gov.pl/web/psse-x/y", "gov.pl"))
        self.assertFalse(same_site("https://lubomia.pl.evil.com/x", "lubomia.pl"))
        self.assertFalse(same_site("https://evillubomia.pl/x", "lubomia.pl"))
        self.assertFalse(same_site("http://169.254.169.254/latest/meta-data", "lubomia.pl"))
        self.assertFalse(same_site("file:///etc/passwd", "lubomia.pl"))

    def test_schedule_pdf_on_a_foreign_host_is_refused(self):
        from sources.waste import month_table_pdf

        page = '<a href="https://evil.example/harmonogram_2027.pdf">Harmonogram wywozu odpadów 2027</a>'
        with mock.patch.object(month_table_pdf, "get", return_value=mock.Mock(text=page)):
            with self.assertRaises(RuntimeError):
                month_table_pdf.find_pdf("https://lubomia.pl/odpady", "harmonogram wywozu odpadów",
                                         ["lubomia.pl", "idcom-jst.pl"])

    def test_schedule_pdf_on_the_gminas_file_host_is_followed(self):
        from sources.waste import month_table_pdf

        page = ('<a href="https://cms-v2-files.idcom-jst.pl/a/harmonogram_2025.pdf">Harmonogram wywozu odpadów 2025</a>'
                '<a href="https://cms-v2-files.idcom-jst.pl/a/harmonogram_2026.pdf">Harmonogram wywozu odpadów w roku 2026</a>')
        with mock.patch.object(month_table_pdf, "get", return_value=mock.Mock(text=page)):
            url, year = month_table_pdf.find_pdf("https://lubomia.pl/odpady", "harmonogram wywozu odpadów",
                                                 ["lubomia.pl", "idcom-jst.pl"])
        self.assertEqual(2026, year)
        self.assertTrue(url.endswith("harmonogram_2026.pdf"))

    def test_off_site_tile_is_not_followed(self):
        from sources.news import tiles_list

        html = """
        <article><time>07.10.2026</time><h3><a href="/aktualnosci-szczegoly/1,ok.html">Ok</a></h3></article>
        <article><time>07.10.2026</time><h3><a href="https://evil.example/aktualnosci-szczegoly/2,x.html">X</a></h3></article>
        """
        found = tiles_list.tiles(html, "https://goksirlubomia.pl/", "aktualnosci-szczegoly/")
        self.assertEqual(["Ok"], [t for _, t, _ in found])


class Paths(unittest.TestCase):

    def test_a_slug_cannot_walk_out_of_cities(self):
        for bad in ("../app", "..", "rybnik/../lubomia", "Rybnik", "x y", ""):
            with self.assertRaises(SystemExit, msg=bad):
                load_ctx(bad)

    def test_an_input_file_cannot_walk_out_of_its_city(self):
        ctx = Ctx(slug="lubomia", city={"name": "Lubomia"}, sources={})
        with self.assertRaises(ValueError):
            ctx.input_file("../rybnik/manual_events.json")
        self.assertTrue(str(ctx.input_file("points.json")).endswith("points.json"))


class Downloads(unittest.TestCase):

    def _response(self, headers, chunks):
        r = mock.Mock()
        r.headers = headers
        r.raise_for_status = mock.Mock()
        r.iter_content = mock.Mock(return_value=iter(chunks))
        r.encoding = "utf-8"
        return r

    def test_a_declared_huge_body_is_refused_before_reading(self):
        r = self._response({"content-length": str(10 ** 10)}, [])
        with mock.patch.object(common.requests, "get", return_value=r):
            with self.assertRaises(TooLarge):
                common.get("https://lubomia.pl/x")
        r.iter_content.assert_not_called()

    def test_an_undeclared_huge_body_is_cut_off(self):
        r = self._response({}, (b"x" * 1024 * 1024 for _ in range(10_000)))
        with mock.patch.object(common.requests, "get", return_value=r):
            with self.assertRaises(TooLarge):
                common.get("https://lubomia.pl/x", max_bytes=5 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
