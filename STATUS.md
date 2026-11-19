# Status danych

Aktualizacja: 2026-11-19T07:23:43 (czas UTC runnera CI). Generowane przez `scraper/health.py` po każdym przebiegu; nie edytuj ręcznie.

Zgłoszenie na GitHubie otwiera się, gdy źródło zawiedzie 2 przebiegi z rzędu, i zamyka samo, gdy wróci.

## lubomia

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-19 07:20 | 18 | lubomia.pl (18) |
| Wiadomości | ✅ | 2026-11-19 07:20 | 70 | GOKSiR Lubomia (16), IMGW (1), Radio 90 (22), lubomia.pl (31) |
| Punkty odpadów | ✅ | 2026-11-19 07:20 | 60 | punkty (1), słownik (59) |
| Sport | ✅ | 2026-11-19 07:20 | 49 | naprzod-syrynia (17), silesia-lubomia (17), wypoczynek-bukow (15) |
| Transport | ✅ | 2026-11-19 07:20 | 93 | przystanki (93) |
| Odpady | ✅ | 2026-11-19 07:20 | 9 | rejony (9) |

## rybnik

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-19 07:23 | 171 | DK Boguszowice (16), DK Chwałowice (6), TZR (25), biletyna.pl (41), iRybnik (83) |
| Wiadomości | ❌ | 2026-11-19 07:23 | 120 | IMGW (1), Radio 90 (30), nowiny.pl (15), rybnik.com.pl (34), rybnik.eu (35), tuRybnik.pl (5) |
| Punkty odpadów | ✅ | 2026-11-19 07:23 | 62 | punkty (3), słownik (59) |
| Sport | ✅ | 2026-11-19 07:23 | 60 | row-1964 (36), row-kobiety (8), row-zuzel (16) |
| Transport | ✅ | 2026-11-19 07:23 | 625 | przystanki (625) |
| Odpady | ✅ | 2026-11-19 07:23 | 98 | rejony (98) |

Źródła zastępcze w użyciu (dane są, ale nie z głównego źródła):

- `news/rybnik.com.pl` przez `google_news` — główne: 403 Client Error: Forbidden for url: https://www.rybnik.com.pl/feed,feed0.html

Problemy:

- `news/tuRybnik.pl` — 32× z rzędu od 2026-11-05T19:58: 403 Client Error: Forbidden for url: https://turybnik.pl/feed/

## zory

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-19 07:19 | 9 | biletyna.pl (5), zory.pl (4) |
| Gazeta | ✅ | 2026-11-19 07:19 | 14 | numery (14) |
| Wiadomości | ✅ | 2026-11-19 07:19 | 100 | IMGW (1), Radio 90 (30), zory.pl (69) |
| Godziny otwarcia | ✅ | 2026-11-19 07:19 | 10 | miejsca (10) |
| Punkty odpadów | ✅ | 2026-11-19 07:19 | 320 | punkty (1), słownik (319) |
| Transport | ❌ | 2026-10-26 04:43 | 187 | przystanki (187) |
| Odpady | ✅ | 2026-11-19 07:19 | 164 | rejony (164) |

Problemy:

- `transit/*` — 61× z rzędu od 2026-10-26T22:41: RuntimeError: no link matching 'GTFS(^/)*\\.zip$' on https://www.zory.pl/dla-mieszkancow/bezplatna-komunikacja-miejska

