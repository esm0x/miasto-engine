# Status danych

Aktualizacja: 2026-11-07T12:58:58 (czas UTC runnera CI). Generowane przez `scraper/health.py` po każdym przebiegu; nie edytuj ręcznie.

Zgłoszenie na GitHubie otwiera się, gdy źródło zawiedzie 2 przebiegi z rzędu, i zamyka samo, gdy wróci.

## lubomia

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-07 12:56 | 19 | lubomia.pl (19) |
| Wiadomości | ✅ | 2026-11-07 12:56 | 73 | GOKSiR Lubomia (18), IMGW (2), Radio 90 (22), lubomia.pl (31) |
| Punkty odpadów | ✅ | 2026-11-07 12:56 | 60 | punkty (1), słownik (59) |
| Sport | ✅ | 2026-11-07 12:56 | 49 | naprzod-syrynia (17), silesia-lubomia (17), wypoczynek-bukow (15) |
| Transport | ✅ | 2026-11-07 12:56 | 93 | przystanki (93) |
| Odpady | ✅ | 2026-11-07 12:56 | 9 | rejony (9) |

## rybnik

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-07 12:58 | 129 | DK Boguszowice (12), DK Chwałowice (5), TZR (29), biletyna.pl (41), iRybnik (42) |
| Wiadomości | ❌ | 2026-11-07 12:58 | 120 | IMGW (2), Radio 90 (30), nowiny.pl (15), rybnik.com.pl (34), rybnik.eu (34), tuRybnik.pl (5) |
| Punkty odpadów | ✅ | 2026-11-07 12:58 | 62 | punkty (3), słownik (59) |
| Sport | ✅ | 2026-11-07 12:58 | 60 | row-1964 (36), row-kobiety (8), row-zuzel (16) |
| Transport | ✅ | 2026-11-07 12:58 | 626 | przystanki (626) |
| Odpady | ✅ | 2026-11-07 12:58 | 98 | rejony (98) |

Źródła zastępcze w użyciu (dane są, ale nie z głównego źródła):

- `news/rybnik.com.pl` przez `google_news` — główne: 403 Client Error: Forbidden for url: https://www.rybnik.com.pl/feed,feed0.html

Problemy:

- `news/tuRybnik.pl` — 5× z rzędu od 2026-11-05T19:58: 403 Client Error: Forbidden for url: https://turybnik.pl/feed/

## zory

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-07 12:56 | 10 | biletyna.pl (5), zory.pl (5) |
| Gazeta | ✅ | 2026-11-07 12:56 | 14 | numery (14) |
| Wiadomości | ✅ | 2026-11-07 12:56 | 100 | IMGW (2), Radio 90 (30), zory.pl (68) |
| Godziny otwarcia | ✅ | 2026-11-07 12:56 | 10 | miejsca (10) |
| Punkty odpadów | ✅ | 2026-11-07 12:56 | 320 | punkty (1), słownik (319) |
| Transport | ❌ | 2026-10-26 04:43 | 187 | przystanki (187) |
| Odpady | ✅ | 2026-11-07 12:56 | 164 | rejony (164) |

Problemy:

- `transit/*` — 34× z rzędu od 2026-10-26T22:41: RuntimeError: no link matching 'GTFS(^/)*\\.zip$' on https://www.zory.pl/dla-mieszkancow/bezplatna-komunikacja-miejska

