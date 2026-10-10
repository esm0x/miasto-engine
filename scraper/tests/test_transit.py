"""Calendar and Trasownik parsing: the parts of a GTFS that are easy to get subtly wrong."""

import unittest
from datetime import date

from bs4 import BeautifulSoup

from engine import plcalendar as cal
from sources.transit import trasownik

SCHOOL = cal.SchoolCalendar({
    "schoolYears": [["2026-09-01", "2027-06-25"]],
    "breaks": [["2026-12-23", "2026-12-31"], ["2027-01-18", "2027-01-31"], ["2027-03-25", "2027-03-30"]],
    "knownUntil": "2027-08-31",
})


class Holidays(unittest.TestCase):

    def test_easter_and_what_hangs_off_it(self):
        self.assertEqual(date(2026, 4, 5), cal.easter(2026))
        self.assertEqual(date(2027, 3, 28), cal.easter(2027))
        h = cal.public_holidays(2027)
        self.assertIn(date(2027, 3, 29), h)   # Easter Monday
        self.assertIn(date(2027, 5, 27), h)   # Corpus Christi
        self.assertIn(date(2027, 5, 16), h)   # Pentecost

    def test_wigilia_is_a_holiday_since_2025(self):
        self.assertIn(date(2026, 12, 24), cal.public_holidays(2026))
        self.assertNotIn(date(2024, 12, 24), cal.public_holidays(2024))


class DayTypes(unittest.TestCase):

    def test_labels_from_the_site(self):
        self.assertEqual(cal.SCHOOL, cal.day_type("Od poniedziałku do piątku - w dni nauki szkolnej oprócz świąt"))
        self.assertEqual(cal.SCHOOL_FREE, cal.day_type("Od poniedziałku do piątku - w dni wolne od nauki szkolnej oprócz świąt"))
        self.assertEqual(cal.SATURDAY, cal.day_type("Soboty oprócz świąt"))
        self.assertEqual(cal.SUNDAY, cal.day_type("Niedziele i święta"))
        self.assertIsNone(cal.day_type("Kursuje w dni targowe"))

    def test_december_mixes_school_break_and_holidays(self):
        days = lambda kind: {d.day for d in cal.service_dates(kind, date(2026, 12, 21), date(2026, 12, 31), SCHOOL)}
        self.assertEqual({21, 22}, days(cal.SCHOOL))
        self.assertEqual({23, 28, 29, 30, 31}, days(cal.SCHOOL_FREE))
        # Wigilia (Thu), Christmas, St Stephen's falling on Saturday, and the Sunday.
        self.assertEqual({24, 25, 26, 27}, days(cal.SUNDAY))
        self.assertEqual(set(), days(cal.SATURDAY))

    def test_winter_holidays_are_school_free(self):
        self.assertFalse(SCHOOL.is_school_day(date(2027, 1, 20)))
        self.assertTrue(SCHOOL.is_school_day(date(2027, 2, 1)))


class TripPage(unittest.TestCase):

    HTML = """
    <div class="day_type">Od poniedziałku do piątku - w dni nauki szkolnej oprócz świąt</div>
    <table>
      <tr><td><a href="przystanek-452.html"><font>WODZISŁAW ŚLĄSKI, TARGOWA DWORZEC AUTOBUSOWY</font></a></td><td>23:50</td></tr>
      <tr><td><a href="przystanek-55.html">SYRYNIA, POWSTAŃCÓW ŚLĄSKICH BUKOWSKA</a></td><td>23:58</td></tr>
      <tr><td><a href="przystanek-60.html">LUBOMIA, NEPOMUCENA PARK</a></td><td>00:04</td></tr>
    </table>"""

    def test_trip_rows_and_midnight(self):
        label, rows = trasownik.parse_trip(BeautifulSoup(self.HTML, "html.parser"))
        self.assertEqual(cal.SCHOOL, cal.day_type(label))
        self.assertEqual(["452", "55", "60"], [r[0] for r in rows])
        self.assertEqual([23 * 60 + 50, 23 * 60 + 58, 24 * 60 + 4], [r[2] for r in rows])
        self.assertEqual("24:04:00", trasownik.hhmmss(rows[-1][2]))

    def test_names_read_like_names(self):
        self.assertEqual("Syrynia, Powstańców Śląskich Szkoła", trasownik.pretty("SYRYNIA, POWSTAŃCÓW ŚLĄSKICH SZKOŁA"))
        self.assertEqual("Wodzisław Śląski, Matuszczyka XXX-lecia", trasownik.pretty("WODZISŁAW ŚLĄSKI, MATUSZCZYKA XXX-LECIA"))

    def test_zip_is_byte_identical_for_identical_content(self):
        files = {"b.txt": b"2", "a.txt": b"1"}
        self.assertEqual(trasownik.build_zip(files), trasownik.build_zip(dict(reversed(list(files.items())))))


if __name__ == "__main__":
    unittest.main()
