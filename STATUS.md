# Status danych

Aktualizacja: 2026-11-28T07:44:56 (czas UTC runnera CI). Generowane przez `scraper/health.py` po każdym przebiegu; nie edytuj ręcznie.

Zgłoszenie na GitHubie otwiera się, gdy źródło zawiedzie 2 przebiegi z rzędu, i zamyka samo, gdy wróci.

## lubomia

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-28 07:43 | 17 | lubomia.pl (17) |
| Wiadomości | ✅ | 2026-11-28 07:43 | 70 | GOKSiR Lubomia (16), IMGW (1), Radio 90 (22), lubomia.pl (31) |
| Punkty odpadów | ✅ | 2026-11-28 07:43 | 60 | punkty (1), słownik (59) |
| Sport | ✅ | 2026-11-28 07:43 | 49 | naprzod-syrynia (17), silesia-lubomia (17), wypoczynek-bukow (15) |
| Transport | ✅ | 2026-11-28 07:43 | 93 | przystanki (93) |
| Odpady | ✅ | 2026-11-28 07:43 | 9 | rejony (9) |

## rybnik

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-28 07:44 | 134 | DK Boguszowice (16), DK Chwałowice (4), TZR (34), biletyna.pl (34), iRybnik (46) |
| Wiadomości | ❌ | 2026-11-28 07:44 | 120 | IMGW (1), Radio 90 (30), nowiny.pl (15), rybnik.com.pl (35), rybnik.eu (34), tuRybnik.pl (5) |
| Punkty odpadów | ✅ | 2026-11-28 07:44 | 62 | punkty (3), słownik (59) |
| Sport | ✅ | 2026-11-28 07:44 | 60 | row-1964 (36), row-kobiety (8), row-zuzel (16) |
| Transport | ✅ | 2026-11-28 07:44 | 622 | przystanki (622) |
| Odpady | ✅ | 2026-11-28 07:44 | 98 | rejony (98) |

Źródła zastępcze w użyciu (dane są, ale nie z głównego źródła):

- `news/rybnik.com.pl` przez `google_news` — główne: 403 Client Error: Forbidden for url: https://www.rybnik.com.pl/feed,feed0.html

Problemy:

- `news/tuRybnik.pl` — 50× z rzędu od 2026-11-05T19:58: 403 Client Error: Forbidden for url: https://turybnik.pl/feed/

## zory

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-28 07:42 | 9 | biletyna.pl (5), zory.pl (4) |
| Gazeta | ✅ | 2026-11-28 07:42 | 14 | numery (14) |
| Wiadomości | ✅ | 2026-11-28 07:42 | 100 | IMGW (1), Radio 90 (30), zory.pl (69) |
| Godziny otwarcia | ✅ | 2026-11-28 07:42 | 10 | miejsca (10) |
| Punkty odpadów | ✅ | 2026-11-28 07:42 | 320 | punkty (1), słownik (319) |
| Transport | ❌ | 2026-10-26 04:43 | 187 | przystanki (187) |
| Odpady | ✅ | 2026-11-28 07:42 | 164 | rejony (164) |

Problemy:

- `transit/*` — 79× z rzędu od 2026-10-26T22:41: RuntimeError: no link matching 'GTFS(^/)*\\.zip$' on https://www.zory.pl/dla-mieszkancow/bezplatna-komunikacja-miejska

