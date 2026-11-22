# Status danych

Aktualizacja: 2026-11-22T19:35:11 (czas UTC runnera CI). Generowane przez `scraper/health.py` po każdym przebiegu; nie edytuj ręcznie.

Zgłoszenie na GitHubie otwiera się, gdy źródło zawiedzie 2 przebiegi z rzędu, i zamyka samo, gdy wróci.

## lubomia

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-22 19:33 | 17 | lubomia.pl (17) |
| Wiadomości | ✅ | 2026-11-22 19:33 | 71 | GOKSiR Lubomia (16), IMGW (1), Radio 90 (23), lubomia.pl (31) |
| Punkty odpadów | ✅ | 2026-11-22 19:33 | 60 | punkty (1), słownik (59) |
| Sport | ✅ | 2026-11-22 19:33 | 49 | naprzod-syrynia (17), silesia-lubomia (17), wypoczynek-bukow (15) |
| Transport | ✅ | 2026-11-22 19:33 | 93 | przystanki (93) |
| Odpady | ✅ | 2026-11-22 19:33 | 9 | rejony (9) |

## rybnik

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ⚠️ | 2026-11-22 19:34 | 114 | DK Boguszowice (14), DK Chwałowice (5), TZR (35), iRybnik (60) |
| Wiadomości | ❌ | 2026-11-22 19:34 | 120 | IMGW (1), Radio 90 (27), nowiny.pl (16), rybnik.com.pl (43), rybnik.eu (28), tuRybnik.pl (5) |
| Punkty odpadów | ✅ | 2026-11-22 19:34 | 62 | punkty (3), słownik (59) |
| Sport | ✅ | 2026-11-22 19:34 | 60 | row-1964 (36), row-kobiety (8), row-zuzel (16) |
| Transport | ✅ | 2026-11-22 19:34 | 622 | przystanki (622) |
| Odpady | ✅ | 2026-11-22 19:34 | 98 | rejony (98) |

Problemy:

- `events/biletyna.pl` — 1× z rzędu od 2026-11-22T19:35: HTTPError: 403 Client Error: Forbidden for url: https://biletyna.pl/Rybnik
- `news/tuRybnik.pl` — 39× z rzędu od 2026-11-05T19:58: 403 Client Error: Forbidden for url: https://turybnik.pl/feed/

## zory

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-22 19:33 | 10 | biletyna.pl (5), zory.pl (5) |
| Gazeta | ✅ | 2026-11-22 19:33 | 14 | numery (14) |
| Wiadomości | ✅ | 2026-11-22 19:33 | 100 | IMGW (1), Radio 90 (30), zory.pl (69) |
| Godziny otwarcia | ✅ | 2026-11-22 19:33 | 10 | miejsca (10) |
| Punkty odpadów | ✅ | 2026-11-22 19:33 | 320 | punkty (1), słownik (319) |
| Transport | ❌ | 2026-10-26 04:43 | 187 | przystanki (187) |
| Odpady | ✅ | 2026-11-22 19:33 | 164 | rejony (164) |

Problemy:

- `transit/*` — 68× z rzędu od 2026-10-26T22:41: RuntimeError: no link matching 'GTFS(^/)*\\.zip$' on https://www.zory.pl/dla-mieszkancow/bezplatna-komunikacja-miejska

