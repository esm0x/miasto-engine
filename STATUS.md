# Status danych

Aktualizacja: 2026-11-16T22:02:34 (czas UTC runnera CI). Generowane przez `scraper/health.py` po każdym przebiegu; nie edytuj ręcznie.

Zgłoszenie na GitHubie otwiera się, gdy źródło zawiedzie 2 przebiegi z rzędu, i zamyka samo, gdy wróci.

## lubomia

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-16 22:01 | 18 | lubomia.pl (18) |
| Wiadomości | ❌ | 2026-11-16 22:01 | 71 | GOKSiR Lubomia (17), IMGW (1), Radio 90 (22), lubomia.pl (31) |
| Punkty odpadów | ✅ | 2026-11-16 22:01 | 60 | punkty (1), słownik (59) |
| Sport | ✅ | 2026-11-16 22:01 | 49 | naprzod-syrynia (17), silesia-lubomia (17), wypoczynek-bukow (15) |
| Transport | ✅ | 2026-11-16 22:01 | 93 | przystanki (93) |
| Odpady | ✅ | 2026-11-16 22:01 | 9 | rejony (9) |

Problemy:

- `news/Sanepid Wodzisław` — 8× z rzędu od 2026-11-13T19:42: HTTPSConnectionPool(host='www.gov.pl', port=443): Max retries exceeded with url: /web/psse-wodzislaw-slaski/komunikaty (Caused by NewConnectionError("HTTPSConne

## rybnik

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-16 22:02 | 155 | DK Boguszowice (16), DK Chwałowice (6), TZR (27), biletyna.pl (20), iRybnik (86) |
| Wiadomości | ❌ | 2026-11-16 22:02 | 120 | IMGW (1), Radio 90 (28), nowiny.pl (15), rybnik.com.pl (43), rybnik.eu (28), tuRybnik.pl (5) |
| Punkty odpadów | ✅ | 2026-11-16 22:02 | 62 | punkty (3), słownik (59) |
| Sport | ✅ | 2026-11-16 22:02 | 60 | row-1964 (36), row-kobiety (8), row-zuzel (16) |
| Transport | ✅ | 2026-11-16 22:02 | 626 | przystanki (626) |
| Odpady | ✅ | 2026-11-16 22:02 | 98 | rejony (98) |

Problemy:

- `news/tuRybnik.pl` — 27× z rzędu od 2026-11-05T19:58: 403 Client Error: Forbidden for url: https://turybnik.pl/feed/

## zory

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-16 22:01 | 9 | biletyna.pl (5), zory.pl (4) |
| Gazeta | ✅ | 2026-11-16 22:01 | 14 | numery (14) |
| Wiadomości | ❌ | 2026-11-16 22:01 | 100 | IMGW (1), Radio 90 (30), zory.pl (69) |
| Godziny otwarcia | ✅ | 2026-11-16 22:01 | 10 | miejsca (10) |
| Punkty odpadów | ✅ | 2026-11-16 22:01 | 320 | punkty (1), słownik (319) |
| Transport | ❌ | 2026-10-26 04:43 | 187 | przystanki (187) |
| Odpady | ✅ | 2026-11-16 22:01 | 164 | rejony (164) |

Problemy:

- `news/Sanepid Rybnik` — 8× z rzędu od 2026-11-13T19:42: HTTPSConnectionPool(host='www.gov.pl', port=443): Max retries exceeded with url: /web/psse-rybnik/komunikaty (Caused by NewConnectionError("HTTPSConnection(host
- `transit/*` — 56× z rzędu od 2026-10-26T22:41: RuntimeError: no link matching 'GTFS(^/)*\\.zip$' on https://www.zory.pl/dla-mieszkancow/bezplatna-komunikacja-miejska

