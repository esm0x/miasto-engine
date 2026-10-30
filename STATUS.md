# Status danych

Aktualizacja: 2026-10-30T05:45:29 (czas UTC runnera CI). Generowane przez `scraper/health.py` po każdym przebiegu; nie edytuj ręcznie.

Zgłoszenie na GitHubie otwiera się, gdy źródło zawiedzie 2 przebiegi z rzędu, i zamyka samo, gdy wróci.

## lubomia

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-10-30 05:44 | 19 | lubomia.pl (19) |
| Wiadomości | ❌ | 2026-10-30 05:44 | 73 | GOKSiR Lubomia (17), IMGW (1), Radio 90 (24), lubomia.pl (31) |
| Punkty odpadów | ✅ | 2026-10-30 05:44 | 60 | punkty (1), słownik (59) |
| Sport | ✅ | 2026-10-30 05:44 | 49 | naprzod-syrynia (17), silesia-lubomia (17), wypoczynek-bukow (15) |
| Transport | ✅ | 2026-10-30 05:44 | 93 | przystanki (93) |
| Odpady | ✅ | 2026-10-30 05:44 | 9 | rejony (9) |

Problemy:

- `news/IMGW` — 3× z rzędu od 2026-10-29T13:00: 404 Client Error: Not Found for url: https://danepubliczne.imgw.pl/api/data/warningshydro

## rybnik

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-10-30 05:45 | 137 | DK Boguszowice (15), DK Chwałowice (4), TZR (32), biletyna.pl (43), iRybnik (43) |
| Wiadomości | ❌ | 2026-10-30 05:45 | 120 | IMGW (1), Radio 90 (30), nowiny.pl (15), rybnik.com.pl (34), rybnik.eu (34), tuRybnik.pl (6) |
| Punkty odpadów | ✅ | 2026-10-30 05:45 | 62 | punkty (3), słownik (59) |
| Sport | ✅ | 2026-10-30 05:45 | 60 | row-1964 (36), row-kobiety (8), row-zuzel (16) |
| Transport | ✅ | 2026-10-30 05:45 | 626 | przystanki (626) |
| Odpady | ✅ | 2026-10-30 05:45 | 98 | rejony (98) |

Źródła zastępcze w użyciu (dane są, ale nie z głównego źródła):

- `news/rybnik.com.pl` przez `google_news` — główne: 403 Client Error: Forbidden for url: https://www.rybnik.com.pl/feed,feed0.html

Problemy:

- `news/IMGW` — 3× z rzędu od 2026-10-29T13:00: 404 Client Error: Not Found for url: https://danepubliczne.imgw.pl/api/data/warningshydro

## zory

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-10-30 05:43 | 7 | biletyna.pl (5), zory.pl (2) |
| Gazeta | ✅ | 2026-10-30 05:43 | 13 | numery (13) |
| Wiadomości | ❌ | 2026-10-30 05:43 | 100 | IMGW (2), Radio 90 (30), zory.pl (68) |
| Godziny otwarcia | ✅ | 2026-10-30 05:43 | 10 | miejsca (10) |
| Punkty odpadów | ✅ | 2026-10-30 05:43 | 320 | punkty (1), słownik (319) |
| Transport | ❌ | 2026-10-26 04:43 | 187 | przystanki (187) |
| Odpady | ✅ | 2026-10-30 05:43 | 164 | rejony (164) |

Problemy:

- `news/IMGW` — 3× z rzędu od 2026-10-29T13:00: 404 Client Error: Not Found for url: https://danepubliczne.imgw.pl/api/data/warningshydro
- `transit/*` — 12× z rzędu od 2026-10-26T22:41: RuntimeError: no link matching 'GTFS(^/)*\\.zip$' on https://www.zory.pl/dla-mieszkancow/bezplatna-komunikacja-miejska

