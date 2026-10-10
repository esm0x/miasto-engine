"""Parsers and rules, on inputs copied from the real sources (October 2026)."""

import unittest
from datetime import datetime

from modules.news import classify
from sources import idcom
from sources.news import govpl
from sources.waste import month_table_pdf as pdf


class AlertWords(unittest.TestCase):
    """The keyword list decides what interrupts people. Both directions matter."""

    ALERTS = [
        "Ogłoszenie w sprawie czasowych utrudnień w ruchu drogowym - Korowód Dożynkowy",
        "Utrudniony przejazd przez Syrynię",
        "Zamknięcie drogi powiatowej",
        "Ulica Jośki w Rybniku zostanie zamknięta",
        "PSZOK NIECZYNNY w dniach 18 - 19 września 2026 r.",
        "Ruch wahadłowy na DK78",
        "Awaria wodociągu na Rudzkiej",
        "stwierdza niezgodność z wartością parametryczną dla wody do spożycia",
        "warunkową przydatność wody do spożycia po przegotowaniu",
    ]
    NOT_ALERTS = [
        "Rozmowy za zamkniętymi drzwiami",
        "Planowane zamknięcie porodówki w Wodzisławiu",
        "Bosak rozpoczyna objazd po Polsce",
        "Konkurs na warunkowe zaliczenie",
        "stwierdza przydatność dla wody do spożycia",
        "Pilot Dromadera o gaszeniu pożarów",
        "Nieczynny sklep z pamiątkami",
    ]

    def test_alerts(self):
        for t in self.ALERTS:
            self.assertEqual("ALERT", classify(t, ""), t)

    def test_not_alerts(self):
        for t in self.NOT_ALERTS:
            self.assertEqual("NORMAL", classify(t, ""), t)


class Idcom(unittest.TestCase):

    def test_news_date(self):
        self.assertEqual(datetime(2026, 9, 15, 12, 40), idcom.parse_date("15 września 2026 godz.  12:40"))

    def test_event_with_hours(self):
        start, end = idcom.parse_when("Kiedy - 23 października 2026 od 16:30 do 21:00")
        self.assertEqual(datetime(2026, 10, 23, 16, 30), start)
        self.assertEqual(datetime(2026, 10, 23, 21, 0), end)

    def test_event_over_several_days(self):
        start, end = idcom.parse_when("26 września 2026 - 28 września 2026")
        self.assertEqual(datetime(2026, 9, 26), start)
        self.assertEqual(datetime(2026, 9, 28), end)

    def test_venue_drops_the_administrative_chain(self):
        raw = ("Lokalizacja - Województwo śląskie, powiat wodzisławski, gmina Lubomia, Nieboczowy, "
               "Wiejski Dom Kultury w Nieboczowach ul. Wiejska 25, Nieboczowy, 44-360 Lubomia")
        self.assertEqual("Wiejski Dom Kultury w Nieboczowach ul. Wiejska 25, Nieboczowy",
                         idcom.venue_from_location(raw))


class GovPl(unittest.TestCase):

    def test_notice_date_from_text(self):
        self.assertEqual(datetime(2026, 7, 12), govpl.notice_date("Materiały Komunikat nr 2 z dnia 12.07.2026 r"))


class SchedulePdf(unittest.TestCase):

    def test_streets_per_village_and_whole_villages(self):
        self.assertEqual(
            [("Syrynia", "3 -Maja"), ("Syrynia", "Musioła"), ("Lubomia", "Potocka")],
            pdf.split_places("Syrynia: 3 -Maja, Musioła - Lubomia: Potocka"),
        )
        self.assertEqual([("Buków", None), ("Grabówka", None)], pdf.split_places("Buków, Grabówka"))

    def test_hyphenated_dates_in_street_names(self):
        self.assertEqual("3 Maja", pdf.tidy_street("3 -Maja"))
        self.assertEqual("8 Maja", pdf.tidy_street("8-Maja"))

    def test_one_entry_per_village_with_shared_pickups(self):
        regions = [{"rejon": "III", "opis": "Buków, Grabówka, Nieboczowy - Syrynia: Dąbrowy",
                    "odbiory": {"ZMIESZANE": {1: [5, 19]}, "POPIOLY": {2: [31]}}}]
        rejony = pdf.to_rejony(regions, 2026)
        by_place = {r["district"]: r for r in rejony}
        self.assertEqual({"Buków", "Grabówka", "Nieboczowy", "Syrynia"}, set(by_place))
        self.assertEqual([{"name": "*", "rules": []}], by_place["Buków"]["streets"])
        self.assertEqual(["Dąbrowy"], [s["name"] for s in by_place["Syrynia"]["streets"]])
        zm = next(p for p in by_place["Buków"]["pickups"] if p["type"] == "ZMIESZANE")
        self.assertEqual(["2026-01-05", "2026-01-19"], zm["dates"])
        # 31 February does not exist; it is skipped, not crashed on or shifted.
        popiol = next(p for p in by_place["Buków"]["pickups"] if p["type"] == "POPIOLY")
        self.assertEqual([], popiol["dates"])


if __name__ == "__main__":
    unittest.main()
