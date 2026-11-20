# Status danych

Aktualizacja: 2026-11-20T07:12:02 (czas UTC runnera CI). Generowane przez `scraper/health.py` po każdym przebiegu; nie edytuj ręcznie.

Zgłoszenie na GitHubie otwiera się, gdy źródło zawiedzie 2 przebiegi z rzędu, i zamyka samo, gdy wróci.

## lubomia

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-20 07:09 | 18 | lubomia.pl (18) |
| Wiadomości | ✅ | 2026-11-20 07:09 | 70 | GOKSiR Lubomia (16), IMGW (1), Radio 90 (22), lubomia.pl (31) |
| Punkty odpadów | ✅ | 2026-11-20 07:09 | 60 | punkty (1), słownik (59) |
| Sport | ✅ | 2026-11-20 07:09 | 49 | naprzod-syrynia (17), silesia-lubomia (17), wypoczynek-bukow (15) |
| Transport | ✅ | 2026-11-20 07:09 | 93 | przystanki (93) |
| Odpady | ✅ | 2026-11-20 07:09 | 9 | rejony (9) |

## rybnik

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-20 07:11 | 155 | DK Boguszowice (16), DK Chwałowice (4), TZR (30), biletyna.pl (29), iRybnik (76) |
| Wiadomości | ❌ | 2026-11-20 07:11 | 120 | IMGW (1), Radio 90 (30), nowiny.pl (15), rybnik.com.pl (35), rybnik.eu (34), tuRybnik.pl (5) |
| Punkty odpadów | ✅ | 2026-11-20 07:11 | 62 | punkty (3), słownik (59) |
| Sport | ✅ | 2026-11-20 07:11 | 60 | row-1964 (36), row-kobiety (8), row-zuzel (16) |
| Transport | ✅ | 2026-11-20 07:11 | 625 | przystanki (625) |
| Odpady | ✅ | 2026-11-20 07:11 | 98 | rejony (98) |

Źródła zastępcze w użyciu (dane są, ale nie z głównego źródła):

- `news/rybnik.com.pl` przez `google_news` — główne: 403 Client Error: Forbidden for url: https://www.rybnik.com.pl/feed,feed0.html

Problemy:

- `news/tuRybnik.pl` — 34× z rzędu od 2026-11-05T19:58: 403 Client Error: Forbidden for url: https://turybnik.pl/feed/

## zory

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-20 07:09 | 11 | biletyna.pl (6), zory.pl (5) |
| Gazeta | ✅ | 2026-11-20 07:09 | 14 | numery (14) |
| Wiadomości | ✅ | 2026-11-20 07:09 | 100 | IMGW (1), Radio 90 (30), zory.pl (69) |
| Godziny otwarcia | ✅ | 2026-11-20 07:09 | 10 | miejsca (10) |
| Punkty odpadów | ✅ | 2026-11-20 07:09 | 320 | punkty (1), słownik (319) |
| Transport | ❌ | 2026-10-26 04:43 | 187 | przystanki (187) |
| Odpady | ✅ | 2026-11-20 07:09 | 164 | rejony (164) |

Problemy:

- `transit/*` — 63× z rzędu od 2026-10-26T22:41: RuntimeError: no link matching 'GTFS(^/)*\\.zip$' on https://www.zory.pl/dla-mieszkancow/bezplatna-komunikacja-miejska

