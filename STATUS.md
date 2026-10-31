# Status danych

Aktualizacja: 2026-10-31T05:37:55 (czas UTC runnera CI). Generowane przez `scraper/health.py` po każdym przebiegu; nie edytuj ręcznie.

Zgłoszenie na GitHubie otwiera się, gdy źródło zawiedzie 2 przebiegi z rzędu, i zamyka samo, gdy wróci.

## lubomia

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-10-31 05:36 | 19 | lubomia.pl (19) |
| Wiadomości | ✅ | 2026-10-31 05:36 | 73 | GOKSiR Lubomia (17), IMGW (1), Radio 90 (24), lubomia.pl (31) |
| Punkty odpadów | ✅ | 2026-10-31 05:36 | 60 | punkty (1), słownik (59) |
| Sport | ✅ | 2026-10-31 05:36 | 49 | naprzod-syrynia (17), silesia-lubomia (17), wypoczynek-bukow (15) |
| Transport | ✅ | 2026-10-31 05:36 | 93 | przystanki (93) |
| Odpady | ✅ | 2026-10-31 05:36 | 9 | rejony (9) |

## rybnik

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-10-31 05:37 | 121 | DK Boguszowice (16), DK Chwałowice (7), TZR (34), biletyna.pl (23), iRybnik (41) |
| Wiadomości | ✅ | 2026-10-31 05:37 | 120 | IMGW (1), Radio 90 (30), nowiny.pl (16), rybnik.com.pl (34), rybnik.eu (33), tuRybnik.pl (6) |
| Punkty odpadów | ✅ | 2026-10-31 05:37 | 62 | punkty (3), słownik (59) |
| Sport | ✅ | 2026-10-31 05:37 | 60 | row-1964 (36), row-kobiety (8), row-zuzel (16) |
| Transport | ✅ | 2026-10-31 05:37 | 630 | przystanki (630) |
| Odpady | ✅ | 2026-10-31 05:37 | 98 | rejony (98) |

Źródła zastępcze w użyciu (dane są, ale nie z głównego źródła):

- `news/rybnik.com.pl` przez `google_news` — główne: 403 Client Error: Forbidden for url: https://www.rybnik.com.pl/feed,feed0.html

## zory

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-10-31 05:35 | 6 | biletyna.pl (5), zory.pl (1) |
| Gazeta | ✅ | 2026-10-31 05:35 | 13 | numery (13) |
| Wiadomości | ✅ | 2026-10-31 05:35 | 100 | IMGW (1), Radio 90 (30), zory.pl (69) |
| Godziny otwarcia | ✅ | 2026-10-31 05:35 | 10 | miejsca (10) |
| Punkty odpadów | ✅ | 2026-10-31 05:35 | 320 | punkty (1), słownik (319) |
| Transport | ❌ | 2026-10-26 04:43 | 187 | przystanki (187) |
| Odpady | ✅ | 2026-10-31 05:35 | 164 | rejony (164) |

Problemy:

- `transit/*` — 15× z rzędu od 2026-10-26T22:41: RuntimeError: no link matching 'GTFS(^/)*\\.zip$' on https://www.zory.pl/dla-mieszkancow/bezplatna-komunikacja-miejska

