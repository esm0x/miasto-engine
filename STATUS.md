# Status danych

Aktualizacja: 2026-11-19T20:33:48 (czas UTC runnera CI). Generowane przez `scraper/health.py` po każdym przebiegu; nie edytuj ręcznie.

Zgłoszenie na GitHubie otwiera się, gdy źródło zawiedzie 2 przebiegi z rzędu, i zamyka samo, gdy wróci.

## lubomia

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-19 20:33 | 18 | lubomia.pl (18) |
| Wiadomości | ⚠️ | 2026-11-19 20:33 | 70 | GOKSiR Lubomia (16), IMGW (1), Radio 90 (22), lubomia.pl (31) |
| Punkty odpadów | ✅ | 2026-11-19 20:33 | 60 | punkty (1), słownik (59) |
| Sport | ✅ | 2026-11-19 20:33 | 49 | naprzod-syrynia (17), silesia-lubomia (17), wypoczynek-bukow (15) |
| Transport | ✅ | 2026-11-19 20:33 | 93 | przystanki (93) |
| Odpady | ✅ | 2026-11-19 20:33 | 9 | rejony (9) |

Problemy:

- `news/Sanepid Wodzisław` — 1× z rzędu od 2026-11-19T20:33: HTTPSConnectionPool(host='www.gov.pl', port=443): Max retries exceeded with url: /web/psse-wodzislaw-slaski/komunikaty (Caused by NewConnectionError("HTTPSConne

## rybnik

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ⚠️ | 2026-11-19 20:32 | 134 | DK Boguszowice (16), DK Chwałowice (6), TZR (36), iRybnik (76) |
| Wiadomości | ❌ | 2026-11-19 20:32 | 120 | IMGW (1), Radio 90 (28), nowiny.pl (16), rybnik.com.pl (42), rybnik.eu (28), tuRybnik.pl (5) |
| Punkty odpadów | ❌ | 2026-11-19 07:23 | 62 | punkty (3), słownik (59) |
| Sport | ✅ | 2026-11-19 20:32 | 60 | row-1964 (36), row-kobiety (8), row-zuzel (16) |
| Transport | ✅ | 2026-11-19 20:32 | 625 | przystanki (625) |
| Odpady | ❌ | 2026-11-19 07:23 | 98 | rejony (98) |

Problemy:

- `events/biletyna.pl` — 1× z rzędu od 2026-11-19T20:33: HTTPError: 403 Client Error: Forbidden for url: https://biletyna.pl/Rybnik
- `news/rybnik.eu/dla-mieszkancow/aktualnosci` — 1× z rzędu od 2026-11-19T20:33: 415 Client Error: Unsupported Media Type for url: https://www.rybnik.eu/dla-mieszkancow/aktualnosci
- `news/rybnik.eu/dla-mieszkancow/aktualnosci/kategoria/inwestycje` — 1× z rzędu od 2026-11-19T20:33: 415 Client Error: Unsupported Media Type for url: https://www.rybnik.eu/dla-mieszkancow/aktualnosci/kategoria/inwestycje
- `news/rybnik.eu/dla-mieszkancow/aktualnosci/kategoria/komunikacja` — 1× z rzędu od 2026-11-19T20:33: 415 Client Error: Unsupported Media Type for url: https://www.rybnik.eu/dla-mieszkancow/aktualnosci/kategoria/komunikacja
- `news/rybnik.eu/dla-mieszkancow/aktualnosci/kategoria/komunikaty` — 1× z rzędu od 2026-11-19T20:33: 415 Client Error: Unsupported Media Type for url: https://www.rybnik.eu/dla-mieszkancow/aktualnosci/kategoria/komunikaty
- `news/tuRybnik.pl` — 33× z rzędu od 2026-11-05T19:58: 403 Client Error: Forbidden for url: https://turybnik.pl/feed/
- `points/*` — 1× z rzędu od 2026-11-19T20:33: ContractError: waste_points.json: 1 contract violation(s) - gpzon: empty address — worse than no entry at all
- `waste/*` — 1× z rzędu od 2026-11-19T20:33: RuntimeError: waste: no rejony for 2026 (()); keeping the previous file

## zory

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-19 20:33 | 11 | biletyna.pl (6), zory.pl (5) |
| Gazeta | ✅ | 2026-11-19 20:33 | 14 | numery (14) |
| Wiadomości | ⚠️ | 2026-11-19 20:33 | 100 | IMGW (1), Radio 90 (30), zory.pl (69) |
| Godziny otwarcia | ✅ | 2026-11-19 20:33 | 10 | miejsca (10) |
| Punkty odpadów | ✅ | 2026-11-19 20:33 | 320 | punkty (1), słownik (319) |
| Transport | ❌ | 2026-10-26 04:43 | 187 | przystanki (187) |
| Odpady | ✅ | 2026-11-19 20:33 | 164 | rejony (164) |

Problemy:

- `news/Sanepid Rybnik` — 1× z rzędu od 2026-11-19T20:33: HTTPSConnectionPool(host='www.gov.pl', port=443): Max retries exceeded with url: /web/psse-rybnik/komunikaty (Caused by NewConnectionError("HTTPSConnection(host
- `transit/*` — 62× z rzędu od 2026-10-26T22:41: RuntimeError: no link matching 'GTFS(^/)*\\.zip$' on https://www.zory.pl/dla-mieszkancow/bezplatna-komunikacja-miejska

