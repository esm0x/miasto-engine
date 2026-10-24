# Status danych

Aktualizacja: 2026-10-24T04:57:02 (czas UTC runnera CI). Generowane przez `scraper/health.py` po każdym przebiegu; nie edytuj ręcznie.

Zgłoszenie na GitHubie otwiera się, gdy źródło zawiedzie 2 przebiegi z rzędu, i zamyka samo, gdy wróci.

## lubomia

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-10-24 04:33 | 19 | lubomia.pl (19) |
| Wiadomości | ✅ | 2026-10-24 04:33 | 73 | GOKSiR Lubomia (16), IMGW (1), Radio 90 (25), lubomia.pl (31) |
| Punkty odpadów | ✅ | 2026-10-24 04:33 | 60 | punkty (1), słownik (59) |
| Sport | ✅ | 2026-10-24 04:33 | 49 | naprzod-syrynia (17), silesia-lubomia (17), wypoczynek-bukow (15) |
| Transport | ✅ | 2026-10-24 04:33 | 93 | przystanki (93) |
| Odpady | ✅ | 2026-10-24 04:33 | 9 | rejony (9) |

## rybnik

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-10-24 04:34 | 130 | DK Boguszowice (14), DK Chwałowice (5), TZR (33), biletyna.pl (33), iRybnik (45) |
| Wiadomości | ✅ | 2026-10-24 04:34 | 120 | IMGW (1), Radio 90 (30), nowiny.pl (15), rybnik.com.pl (34), rybnik.eu (34), tuRybnik.pl (6) |
| Punkty odpadów | ✅ | 2026-10-24 04:34 | 62 | punkty (3), słownik (59) |
| Sport | ✅ | 2026-10-24 04:34 | 60 | row-1964 (36), row-kobiety (8), row-zuzel (16) |
| Transport | ❌ | 2026-10-22 04:42 | 626 | przystanki (626) |
| Odpady | ✅ | 2026-10-24 04:34 | 98 | rejony (98) |

Źródła zastępcze w użyciu (dane są, ale nie z głównego źródła):

- `news/rybnik.com.pl` przez `google_news` — główne: 403 Client Error: Forbidden for url: https://www.rybnik.com.pl/feed,feed0.html

Problemy:

- `transit/*` — 8× z rzędu od 2026-10-22T12:12: HTTPError: 404 Client Error: Not Found for url: https://km.rybnik.pl/download/attachment/633/gtfs.zip

## zory

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-10-23 21:23 | 8 | biletyna.pl (5), zory.pl (3) |
| Gazeta | ✅ | 2026-10-23 21:23 | 13 | numery (13) |
| Wiadomości | ✅ | 2026-10-23 21:23 | 91 | IMGW (1), Radio 90 (30), zory.pl (60) |
| Godziny otwarcia | ✅ | 2026-10-23 21:23 | 10 | miejsca (10) |
| Punkty odpadów | ✅ | 2026-10-23 21:23 | 320 | punkty (1), słownik (319) |
| Transport | ✅ | 2026-10-23 21:23 | 187 | przystanki (187) |
| Odpady | ✅ | 2026-10-23 21:23 | 164 | rejony (164) |

Problemy:

- `*/raport` — 1× z rzędu od 2026-10-24T04:57: miasto nie przysłało raportu w tym przebiegu (zadanie CI padło?)

