# Status danych

Aktualizacja: 2026-11-26T21:29:08 (czas UTC runnera CI). Generowane przez `scraper/health.py` po każdym przebiegu; nie edytuj ręcznie.

Zgłoszenie na GitHubie otwiera się, gdy źródło zawiedzie 2 przebiegi z rzędu, i zamyka samo, gdy wróci.

## lubomia

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ⚠️ | 2026-11-26 21:28 | 17 | lubomia.pl (17) |
| Wiadomości | ✅ | 2026-11-26 21:28 | 71 | GOKSiR Lubomia (16), IMGW (2), Radio 90 (22), lubomia.pl (31) |
| Punkty odpadów | ✅ | 2026-11-26 21:28 | 60 | punkty (1), słownik (59) |
| Sport | ✅ | 2026-11-26 21:28 | 49 | naprzod-syrynia (17), silesia-lubomia (17), wypoczynek-bukow (15) |
| Transport | ✅ | 2026-11-26 21:28 | 93 | przystanki (93) |
| Odpady | ✅ | 2026-11-26 21:28 | 9 | rejony (9) |

Problemy:

- `events/biletyna.pl` — 1× z rzędu od 2026-11-26T21:29: HTTPError: 403 Client Error: Forbidden for url: https://biletyna.pl/Lubomia

## rybnik

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ⚠️ | 2026-11-26 21:28 | 111 | DK Boguszowice (17), DK Chwałowice (5), TZR (39), iRybnik (50) |
| Wiadomości | ❌ | 2026-11-26 21:28 | 120 | IMGW (2), Radio 90 (28), nowiny.pl (15), rybnik.com.pl (43), rybnik.eu (27), tuRybnik.pl (5) |
| Punkty odpadów | ❌ | 2026-11-26 08:13 | 62 | punkty (3), słownik (59) |
| Sport | ✅ | 2026-11-26 21:28 | 60 | row-1964 (36), row-kobiety (8), row-zuzel (16) |
| Transport | ✅ | 2026-11-26 21:28 | 622 | przystanki (622) |
| Odpady | ❌ | 2026-11-26 08:13 | 98 | rejony (98) |

Problemy:

- `events/biletyna.pl` — 1× z rzędu od 2026-11-26T21:29: HTTPError: 403 Client Error: Forbidden for url: https://biletyna.pl/Rybnik
- `news/rybnik.eu/dla-mieszkancow/aktualnosci` — 1× z rzędu od 2026-11-26T21:29: 415 Client Error: Unsupported Media Type for url: https://www.rybnik.eu/dla-mieszkancow/aktualnosci
- `news/rybnik.eu/dla-mieszkancow/aktualnosci/kategoria/inwestycje` — 1× z rzędu od 2026-11-26T21:29: 415 Client Error: Unsupported Media Type for url: https://www.rybnik.eu/dla-mieszkancow/aktualnosci/kategoria/inwestycje
- `news/rybnik.eu/dla-mieszkancow/aktualnosci/kategoria/komunikacja` — 1× z rzędu od 2026-11-26T21:29: 415 Client Error: Unsupported Media Type for url: https://www.rybnik.eu/dla-mieszkancow/aktualnosci/kategoria/komunikacja
- `news/rybnik.eu/dla-mieszkancow/aktualnosci/kategoria/komunikaty` — 1× z rzędu od 2026-11-26T21:29: 415 Client Error: Unsupported Media Type for url: https://www.rybnik.eu/dla-mieszkancow/aktualnosci/kategoria/komunikaty
- `news/tuRybnik.pl` — 47× z rzędu od 2026-11-05T19:58: 403 Client Error: Forbidden for url: https://turybnik.pl/feed/
- `points/*` — 1× z rzędu od 2026-11-26T21:29: ContractError: waste_points.json: 1 contract violation(s) - gpzon: empty address — worse than no entry at all
- `waste/*` — 1× z rzędu od 2026-11-26T21:29: RuntimeError: waste: no rejony for 2026 (()); keeping the previous file

## zory

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-26 21:28 | 9 | biletyna.pl (5), zory.pl (4) |
| Gazeta | ✅ | 2026-11-26 21:28 | 14 | numery (14) |
| Wiadomości | ✅ | 2026-11-26 21:28 | 100 | IMGW (2), Radio 90 (30), zory.pl (68) |
| Godziny otwarcia | ✅ | 2026-11-26 21:28 | 10 | miejsca (10) |
| Punkty odpadów | ✅ | 2026-11-26 21:28 | 320 | punkty (1), słownik (319) |
| Transport | ❌ | 2026-10-26 04:43 | 187 | przystanki (187) |
| Odpady | ✅ | 2026-11-26 21:28 | 164 | rejony (164) |

Problemy:

- `transit/*` — 76× z rzędu od 2026-10-26T22:41: RuntimeError: no link matching 'GTFS(^/)*\\.zip$' on https://www.zory.pl/dla-mieszkancow/bezplatna-komunikacja-miejska

