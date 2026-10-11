"""Regression tests for the October 2026 review of the Żory additions (hostile inputs)."""

import io
import unittest
import zipfile
from datetime import date
from unittest import mock

from bs4 import BeautifulSoup

import health
from engine import contract
from sources.gazette import typo3_figures
from sources.transit import gtfs_link
from sources.waste import zory_typo3 as z

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def docx_with(body: str) -> bytes:
    xml = f'<w:document xmlns:w="{W_NS}"><w:body>{body}</w:body></w:document>'
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("word/document.xml", xml)
    return buf.getvalue()


class Docx(unittest.TestCase):
    def test_huge_grid_span_is_clamped(self):
        cell = '<w:tc><w:tcPr><w:gridSpan w:val="50000000"/></w:tcPr><w:p><w:r><w:t>x</w:t></w:r></w:p></w:tc>'
        rows = z.docx_tables(docx_with(f"<w:tbl><w:tr>{cell}</w:tr></w:tbl>"))
        self.assertEqual(z.MAX_SPAN, len(rows[0][0]))

    def test_non_numeric_grid_span_is_one_column(self):
        cell = '<w:tc><w:tcPr><w:gridSpan w:val="``` [x](https://e)"/></w:tcPr><w:p/></w:tc>'
        self.assertEqual(1, len(z.docx_tables(docx_with(f"<w:tbl><w:tr>{cell}</w:tr></w:tbl>"))[0][0]))

    def test_oversized_document_xml_is_refused_before_reading(self):
        with mock.patch.object(z, "MAX_XML_BYTES", 100):
            with self.assertRaises(ValueError):
                z.docx_tables(docx_with("<w:p>" + "a" * 500 + "</w:p>"))

    def test_an_address_with_thousands_of_numbers_fails_the_file(self):
        rows = '<w:tr><w:tc><w:p><w:r><w:t>Ulica</w:t></w:r></w:p></w:tc><w:tc><w:p/></w:tc><w:tc><w:p/></w:tc></w:tr>'
        nums = ", ".join(str(i) for i in range(1, 2000))
        rows += ('<w:tr><w:tc><w:p><w:r><w:t>Centralna</w:t></w:r></w:p></w:tc>'
                 f'<w:tc><w:p><w:r><w:t>{nums}</w:t></w:r></w:p></w:tc>'
                 '<w:tc><w:p><w:r><w:t>raz w tygodniu środa</w:t></w:r></w:p></w:tc></w:tr>')
        with self.assertRaises(ValueError):
            z.parse_multi([("x_ZMIESZANYCH.docx", docx_with(f"<w:tbl>{rows}</w:tbl>"))], 2026)


class Gtfs(unittest.TestCase):
    def fetch(self, members: dict[str, bytes]):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for k, v in members.items():
                zf.writestr(k, v)
        ctx = mock.MagicMock()
        ctx.today = date(2026, 10, 12)
        ctx.city = {"dataBaseUrl": "https://example.org/data/x/"}
        written = {}
        ctx.data_dir.__truediv__ = lambda _self, name: mock.MagicMock(write_bytes=lambda b: written.setdefault(name, b))
        resp = mock.MagicMock(content=buf.getvalue())
        with mock.patch.object(gtfs_link, "find_link", return_value="https://www.zory.pl/x/GTFS.zip"), \
             mock.patch.object(gtfs_link, "get", return_value=resp):
            gtfs_link.fetch({"page": "https://www.zory.pl/", "hosts": ["zory.pl"]}, ctx)
        return zipfile.ZipFile(io.BytesIO(written["gtfs.zip"]))

    BASE = {
        "agency.txt": b"agency_id,agency_name\n1,A\n",
        "stops.txt": b"stop_id,stop_name\n1,Rynek\n",
        "routes.txt": b"route_id,route_short_name\n1,01\n",
        "trips.txt": b"route_id,service_id,trip_id\n1,S,T\n",
        "stop_times.txt": b"trip_id,stop_id\nT,1\n",
        "calendar_dates.txt": b"service_id,date,exception_type\nS,20261012,1\n",
    }

    def test_published_zip_has_only_root_gtfs_files(self):
        out = self.fetch({**self.BASE, "x/stops.txt": b"stop_id,stop_name\n9,Evil\n", "README.exe": b"MZ"})
        self.assertEqual(sorted(self.BASE), sorted(out.namelist()))
        self.assertIn(b"Rynek", out.read("stops.txt"))

    def test_member_over_the_limit_is_refused(self):
        with mock.patch.object(gtfs_link, "MAX_MEMBER", 10):
            with self.assertRaises(RuntimeError):
                self.fetch(self.BASE)


class Gazette(unittest.TestCase):
    def fig(self, caption: str):
        html = (f'<figure><a href="/f/kz012026.pdf"><img src="/c.png"></a>'
                f"<figcaption>{caption}</figcaption></figure>")
        return typo3_figures.issue_from(BeautifulSoup(html, "html.parser").figure,
                                        "https://www.zory.pl/", ["zory.pl"], typo3_figures.re.compile("kz"))

    def test_implausible_issue_is_not_an_issue(self):
        self.assertIsNone(self.fig("Nr 99 2099 PILNE"))
        self.assertIsNone(self.fig("Nr 6, wrzesień 2026 " + "x" * 100))
        self.assertEqual("2026-06", self.fig("Nr 6, wrzesień 2026")["id"])

    def test_contract_rejects_future_year(self):
        issue = {"id": "2099-99", "number": 99, "year": 2099, "label": "x", "pdfUrl": "https://a/b.pdf"}
        with self.assertRaises(contract.ContractError):
            contract.check_gazette({"generated_at": "x", "failures": [], "title": "K", "issues": [issue]})


class Places(unittest.TestCase):
    def test_phone_must_look_like_a_phone(self):
        place = {"id": "a", "name": "A", "kind": "INNE", "phone": "123#*31#", "hours": None}
        with self.assertRaises(contract.ContractError):
            contract.check_places({"generated_at": "x", "failures": [], "places": [place]})


class Health(unittest.TestCase):
    def test_error_text_cannot_break_out_of_the_issue(self):
        s = health.safe_text("bad '```\n[click](https://evil) @owner <b>'")
        for bad in ("`", "[", "@", "\n", "<"):
            self.assertNotIn(bad, s)


if __name__ == "__main__":
    unittest.main()
