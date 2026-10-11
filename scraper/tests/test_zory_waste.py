"""Żory's waste parser, on fragments copied from the 2026 PDF and Word files (October 2026)."""

import io
import unittest
import zipfile
from datetime import date

from sources.waste import zory_typo3 as z

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def docx(*rows: list) -> bytes:
    """A minimal .docx with one table. A cell is text, or (text, gridSpan)."""
    def cell(c):
        text, span = (c, 1) if isinstance(c, str) else c
        pr = f'<w:tcPr><w:gridSpan w:val="{span}"/></w:tcPr>' if span > 1 else ""
        return f"<w:tc>{pr}<w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:tc>"
    body = "".join("<w:tr>" + "".join(cell(c) for c in r) + "</w:tr>" for r in rows)
    xml = f'<w:document xmlns:w="{W_NS}"><w:body><w:tbl>{body}</w:tbl></w:body></w:document>'
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("word/document.xml", xml)
    return buf.getvalue()


MONTHS = ["STYCZEŃ", "LUTY", "MARZEC", "KWIECIEŃ", "MAJ", "CZERWIEC", "LIPIEC",
          "SIERPIEŃ", "WRZESIEŃ", "PAŹDZIERNIK", "LISTOPAD", "GRUDZIEŃ"]


class Numbers(unittest.TestCase):
    def rules(self, spec):
        return [(r["from"], r["to"]) for r in z.number_rules(spec)]

    def test_forms_from_the_pdf(self):
        self.assertEqual([(11, 11)], self.rules("11, 11A"))
        self.assertEqual([(106, 106), (108, 108)], self.rules("106 A-C, 108, 108 A-B"))
        self.assertEqual([(None, 20)], self.rules("do nr 20"))
        self.assertEqual([(22, 32)], self.rules("od nr 22 do nr 32"))
        self.assertEqual([(30, 30), (32, 32), (34, 34)], self.rules("30, 32 34"))   # comma missing
        self.assertEqual([(1, 1), (3, 3)], self.rules("1 i 3"))
        self.assertEqual([(25, 37)], self.rules("25-37"))
        self.assertEqual([(45, 45)], self.rules("45 C - I"))
        self.assertEqual([], self.rules(""))


class Streets(unittest.TestCase):
    def test_glued_and_prefixed(self):
        got = z.split_streets("Gajowa 45 C-I, Giedroycia 5, 6, 8, 10Piastów Górnośląskich 4, "
                              "al. Zjednoczonej Europy 29, 16A-BAstrów 8,10")
        self.assertEqual(["Gajowa", "Giedroycia", "Piastów Górnośląskich", "al. Zjednoczonej Europy", "Astrów"],
                         [n for n, _ in got])
        self.assertEqual("29, 16A-B", got[3][1])

    def test_number_then_street_without_comma(self):
        got = z.split_streets("Brzozowa 41,43 Chlebowa 7, Wojska Polskiego 4B-E, 27 al. Zjednoczonej Europy 29")
        self.assertEqual(["Brzozowa", "Chlebowa", "Wojska Polskiego", "al. Zjednoczonej Europy"], [n for n, _ in got])

    def test_streets_named_after_dates(self):
        got = z.split_streets("Górna 2, 3 Maja 4,6, 11 Listopada")
        self.assertEqual([("Górna", "2"), ("3 Maja", "4, 6"), ("11 Listopada", "")], got)

    def test_osiedle_700_lecia_is_not_number_700(self):
        self.assertEqual([("oś. 700-lecia", ""), ("oś. Korfantego", "")],
                         [(z.canon(n), r) for n, r in z.split_streets("oś. 700 lecia, oś. Korfantego")])

    def test_one_street_one_key(self):
        self.assertEqual(z.key("J. Giedroycia"), z.key("Giedroycia"))
        self.assertEqual(z.key("al. Wojska Polskiego"), z.key("Aleja Wojska Polskiego"))
        self.assertEqual(z.key("oś Sikorskiego"), z.key("oś. Sikorskiego"))
        self.assertEqual("Alojzego Frysza", z.canon("Alojzego – Frysza"))
        self.assertEqual("Gustawa Herrlinga-Grudzińskiego", z.canon("Gustawa Herrlinga- Grudzińskiego"))


class Dates(unittest.TestCase):
    def test_value_belongs_to_the_month_header_before_it(self):
        # The 37-column tables: "16,30" one column right of Kwiecień is April.
        cols = {1: 1, 4: 2, 7: 3, 10: 4, 13: 5}
        self.assertEqual(4, z.month_of(11, cols))
        self.assertEqual(5, z.month_of(13, cols))
        self.assertIsNone(z.month_of(0, cols))

    def test_weekly_skips_public_holidays(self):
        tuesdays = z.weekly_dates("raz w tygodniu wtorek", 2026, [1])
        self.assertNotIn("2026-01-06", tuesdays)            # Trzech Króli
        self.assertEqual(["2026-01-13", "2026-01-20", "2026-01-27"], tuesdays)
        mwf = z.weekly_dates("3 razy w tygodniu poniedziałek-środa-piątek", 2026, [4])
        self.assertNotIn("2026-04-06", mwf)                 # Poniedziałek Wielkanocny
        self.assertIn("2026-04-08", mwf)

    def test_holidays_2026(self):
        h = z.holidays(2026)
        for d in (date(2026, 4, 5), date(2026, 5, 24), date(2026, 6, 4), date(2026, 12, 24)):
            self.assertIn(d, h)


class MultiFamily(unittest.TestCase):
    def test_layouts_and_buildings(self):
        mixed = docx(["Ulica", "Nr", "Harmonogram"],
                     ["3 Maja", "4,6", "raz w tygodniu środa"],
                     ["Aleja Wojska Polskiego", "4, 21, 27", "3 razy w tygodniu poniedziałek-środa-piątek"],
                     ["oś. Powstańców Śląskich", "\xa0", "raz w tygodniu środa"])
        paper = docx(["ADRES"] + MONTHS,
                     ["al. Wojska Polskiego, oś Powstańców"] + ["1 raz w tygodniu poniedziałek"] * 12,
                     ["Górna 2, 3 Maja 4,6"] + ["7,21", "4,18"] + [""] * 10)
        ash = docx(["al. Wojska Polskiego 1 a, b, c, 4-27"],
                   MONTHS[:5],
                   ["14", "18", "18", "16", "14"])
        electro = docx(["ADRES"] + MONTHS,
                       ["3 Maja 4,6", ("27.02 – Elektro 27.03 - Opony", 6), ("06.11 – Elektro 06.11 – Opony", 6)])
        rejony, problems = z.parse_multi([
            ("x/HARMONOGRAM_ZMIESZANYCH_WIELORODZINNA.docx", mixed),
            ("x/HARMONOGRAM_PAPIER_PLASTIK_WIELORODZINNA.docx", paper),
            ("x/HARMONOGRAM_ODPADY_POPIOL_WIELORODZINNA.docx", ash),
            ("x/HARMONOGRAM_ELEKTRONIKA_WIELORODZINNA.docx", electro),
        ], 2026)

        def rejon_of(street, n):
            for r in rejony:
                for s in r["streets"]:
                    if s["name"] == street and (not s["rules"] and n is None or any(x["from"] == n for x in s["rules"])):
                        return {p["type"]: p["dates"] for p in r["pickups"]}
            self.fail(f"{street} {n} not found")

        may3 = rejon_of("3 Maja", 4)
        self.assertEqual(["2026-01-07", "2026-01-21", "2026-02-04", "2026-02-18"], may3["PAPIER_PLASTIK"])
        self.assertEqual(["2026-02-27", "2026-11-06"], may3["ELEKTRO"])
        self.assertEqual(["2026-03-27", "2026-11-06"], may3["OPONY"])
        self.assertIn("2026-01-07", may3["ZMIESZANE"])

        # The range 4-27 gives ash dates to buildings 4, 21 and 27 and makes no others.
        wp4 = rejon_of("Aleja Wojska Polskiego", 4)
        self.assertEqual("2026-01-14", wp4["POPIOLY"][0])
        self.assertIn("2026-01-05", wp4["PAPIER_PLASTIK"])  # whole-street Monday collection
        names = {(s["name"], x["from"]) for r in rejony for s in r["streets"] for x in s["rules"]}
        self.assertNotIn(("Aleja Wojska Polskiego", 10), names)

        # "oś Powstańców" in one file and "oś. Powstańców Śląskich" in another: one estate.
        estate = rejon_of("oś. Powstańców Śląskich", None)
        self.assertIn("ZMIESZANE", estate)
        self.assertIn("PAPIER_PLASTIK", estate)
        self.assertTrue(any("ujednolicone" in p for p in problems))

    def test_second_file_for_a_fraction_is_skipped(self):
        f = docx(["Ulica", "Nr", "Harmonogram"], ["Rynek", "24", "raz w tygodniu środa"])
        _, problems = z.parse_multi([("a/X_ZMIESZANYCH.docx", f), ("b/Y_ZMIESZANYCH.docx", f)], 2026)
        self.assertTrue(any("drugi plik" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
