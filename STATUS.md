# Status danych

Aktualizacja: 2026-11-27T08:23:01 (czas UTC runnera CI). Generowane przez `scraper/health.py` po każdym przebiegu; nie edytuj ręcznie.

Zgłoszenie na GitHubie otwiera się, gdy źródło zawiedzie 2 przebiegi z rzędu, i zamyka samo, gdy wróci.

## lubomia

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-27 08:22 | 17 | lubomia.pl (17) |
| Wiadomości | ✅ | 2026-11-27 08:22 | 71 | GOKSiR Lubomia (16), IMGW (2), Radio 90 (22), lubomia.pl (31) |
| Punkty odpadów | ✅ | 2026-11-27 08:22 | 60 | punkty (1), słownik (59) |
| Sport | ✅ | 2026-11-27 08:22 | 49 | naprzod-syrynia (17), silesia-lubomia (17), wypoczynek-bukow (15) |
| Transport | ✅ | 2026-11-27 08:22 | 93 | przystanki (93) |
| Odpady | ✅ | 2026-11-27 08:22 | 9 | rejony (9) |

## rybnik

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-27 08:22 | 133 | DK Boguszowice (17), DK Chwałowice (4), TZR (32), biletyna.pl (30), iRybnik (50) |
| Wiadomości | ❌ | 2026-11-27 08:22 | 120 | IMGW (2), Radio 90 (30), nowiny.pl (15), rybnik.com.pl (41), rybnik.eu (27), tuRybnik.pl (5) |
| Punkty odpadów | ❌ | 2026-11-26 08:13 | 62 | punkty (3), słownik (59) |
| Sport | ✅ | 2026-11-27 08:22 | 60 | row-1964 (36), row-kobiety (8), row-zuzel (16) |
| Transport | ✅ | 2026-11-27 08:22 | 622 | przystanki (622) |
| Odpady | ❌ | 2026-11-26 08:13 | 98 | rejony (98) |

Źródła zastępcze w użyciu (dane są, ale nie z głównego źródła):

- `news/rybnik.com.pl` przez `google_news` — główne: 403 Client Error: Forbidden for url: https://www.rybnik.com.pl/feed,feed0.html

Problemy:

- `news/rybnik.eu/dla-mieszkancow/aktualnosci` — 2× z rzędu od 2026-11-26T21:29: 415 Client Error: Unsupported Media Type for url: https://www.rybnik.eu/dla-mieszkancow/aktualnosci
- `news/rybnik.eu/dla-mieszkancow/aktualnosci/kategoria/inwestycje` — 2× z rzędu od 2026-11-26T21:29: 415 Client Error: Unsupported Media Type for url: https://www.rybnik.eu/dla-mieszkancow/aktualnosci/kategoria/inwestycje
- `news/rybnik.eu/dla-mieszkancow/aktualnosci/kategoria/komunikacja` — 2× z rzędu od 2026-11-26T21:29: 415 Client Error: Unsupported Media Type for url: https://www.rybnik.eu/dla-mieszkancow/aktualnosci/kategoria/komunikacja
- `news/rybnik.eu/dla-mieszkancow/aktualnosci/kategoria/komunikaty` — 2× z rzędu od 2026-11-26T21:29: 415 Client Error: Unsupported Media Type for url: https://www.rybnik.eu/dla-mieszkancow/aktualnosci/kategoria/komunikaty
- `news/tuRybnik.pl` — 48× z rzędu od 2026-11-05T19:58: 403 Client Error: Forbidden for url: https://turybnik.pl/feed/
- `points/*` — 2× z rzędu od 2026-11-26T21:29: ContractError: waste_points.json: 1 contract violation(s) - gpzon: empty address — worse than no entry at all
- `waste/*` — 2× z rzędu od 2026-11-26T21:29: RuntimeError: waste: no rejony for 2026 (()); keeping the previous file

## zory

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-27 08:22 | 9 | biletyna.pl (5), zory.pl (4) |
| Gazeta | ✅ | 2026-11-27 08:22 | 14 | numery (14) |
| Wiadomości | ✅ | 2026-11-27 08:22 | 100 | IMGW (2), Radio 90 (30), zory.pl (68) |
| Godziny otwarcia | ✅ | 2026-11-27 08:22 | 10 | miejsca (10) |
| Punkty odpadów | ✅ | 2026-11-27 08:22 | 320 | punkty (1), słownik (319) |
| Transport | ❌ | 2026-10-26 04:43 | 187 | przystanki (187) |
| Odpady | ✅ | 2026-11-27 08:22 | 164 | rejony (164) |

Problemy:

- `transit/*` — 77× z rzędu od 2026-10-26T22:41: RuntimeError: no link matching 'GTFS(^/)*\\.zip$' on https://www.zory.pl/dla-mieszkancow/bezplatna-komunikacja-miejska

