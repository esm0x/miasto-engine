# Status danych

Aktualizacja: 2026-11-21T07:04:34 (czas UTC runnera CI). Generowane przez `scraper/health.py` po każdym przebiegu; nie edytuj ręcznie.

Zgłoszenie na GitHubie otwiera się, gdy źródło zawiedzie 2 przebiegi z rzędu, i zamyka samo, gdy wróci.

## lubomia

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-21 07:02 | 18 | lubomia.pl (18) |
| Wiadomości | ✅ | 2026-11-21 07:02 | 71 | GOKSiR Lubomia (16), IMGW (1), Radio 90 (23), lubomia.pl (31) |
| Punkty odpadów | ✅ | 2026-11-21 07:02 | 60 | punkty (1), słownik (59) |
| Sport | ✅ | 2026-11-21 07:02 | 49 | naprzod-syrynia (17), silesia-lubomia (17), wypoczynek-bukow (15) |
| Transport | ✅ | 2026-11-21 07:02 | 93 | przystanki (93) |
| Odpady | ✅ | 2026-11-21 07:02 | 9 | rejony (9) |

## rybnik

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-21 07:04 | 170 | DK Boguszowice (16), DK Chwałowice (4), TZR (29), biletyna.pl (51), iRybnik (70) |
| Wiadomości | ❌ | 2026-11-21 07:04 | 120 | IMGW (1), Radio 90 (30), nowiny.pl (15), rybnik.com.pl (34), rybnik.eu (35), tuRybnik.pl (5) |
| Punkty odpadów | ✅ | 2026-11-21 07:04 | 62 | punkty (3), słownik (59) |
| Sport | ✅ | 2026-11-21 07:04 | 60 | row-1964 (36), row-kobiety (8), row-zuzel (16) |
| Transport | ✅ | 2026-11-21 07:04 | 622 | przystanki (622) |
| Odpady | ✅ | 2026-11-21 07:04 | 98 | rejony (98) |

Źródła zastępcze w użyciu (dane są, ale nie z głównego źródła):

- `news/rybnik.com.pl` przez `google_news` — główne: 403 Client Error: Forbidden for url: https://www.rybnik.com.pl/feed,feed0.html

Problemy:

- `news/tuRybnik.pl` — 36× z rzędu od 2026-11-05T19:58: 403 Client Error: Forbidden for url: https://turybnik.pl/feed/

## zory

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-21 07:01 | 12 | biletyna.pl (7), zory.pl (5) |
| Gazeta | ✅ | 2026-11-21 07:01 | 14 | numery (14) |
| Wiadomości | ✅ | 2026-11-21 07:01 | 100 | IMGW (1), Radio 90 (30), zory.pl (69) |
| Godziny otwarcia | ✅ | 2026-11-21 07:01 | 10 | miejsca (10) |
| Punkty odpadów | ✅ | 2026-11-21 07:01 | 320 | punkty (1), słownik (319) |
| Transport | ❌ | 2026-10-26 04:43 | 187 | przystanki (187) |
| Odpady | ✅ | 2026-11-21 07:01 | 164 | rejony (164) |

Problemy:

- `transit/*` — 65× z rzędu od 2026-10-26T22:41: RuntimeError: no link matching 'GTFS(^/)*\\.zip$' on https://www.zory.pl/dla-mieszkancow/bezplatna-komunikacja-miejska

