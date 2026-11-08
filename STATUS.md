# Status danych

Aktualizacja: 2026-11-08T22:05:43 (czas UTC runnera CI). Generowane przez `scraper/health.py` po każdym przebiegu; nie edytuj ręcznie.

Zgłoszenie na GitHubie otwiera się, gdy źródło zawiedzie 2 przebiegi z rzędu, i zamyka samo, gdy wróci.

## lubomia

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-08 22:01 | 19 | lubomia.pl (19) |
| Wiadomości | ✅ | 2026-11-08 22:01 | 72 | GOKSiR Lubomia (18), IMGW (1), Radio 90 (22), lubomia.pl (31) |
| Punkty odpadów | ✅ | 2026-11-08 22:01 | 60 | punkty (1), słownik (59) |
| Sport | ✅ | 2026-11-08 22:01 | 49 | naprzod-syrynia (17), silesia-lubomia (17), wypoczynek-bukow (15) |
| Transport | ✅ | 2026-11-08 22:01 | 93 | przystanki (93) |
| Odpady | ✅ | 2026-11-08 22:01 | 9 | rejony (9) |

## rybnik

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-08 22:05 | 122 | DK Boguszowice (14), DK Chwałowice (4), TZR (27), biletyna.pl (37), iRybnik (40) |
| Wiadomości | ❌ | 2026-11-08 22:05 | 120 | IMGW (1), Radio 90 (30), nowiny.pl (15), rybnik.com.pl (35), rybnik.eu (34), tuRybnik.pl (5) |
| Punkty odpadów | ✅ | 2026-11-08 22:05 | 62 | punkty (3), słownik (59) |
| Sport | ✅ | 2026-11-08 22:05 | 60 | row-1964 (36), row-kobiety (8), row-zuzel (16) |
| Transport | ❌ | 2026-11-08 13:20 | 626 | przystanki (626) |
| Odpady | ✅ | 2026-11-08 22:05 | 98 | rejony (98) |

Źródła zastępcze w użyciu (dane są, ale nie z głównego źródła):

- `news/rybnik.com.pl` przez `google_news` — główne: 403 Client Error: Forbidden for url: https://www.rybnik.com.pl/feed,feed0.html

Problemy:

- `news/tuRybnik.pl` — 9× z rzędu od 2026-11-05T19:58: 403 Client Error: Forbidden for url: https://turybnik.pl/feed/
- `transit/*` — 1× z rzędu od 2026-11-08T22:05: ReadTimeout: HTTPSConnectionPool(host='km.rybnik.pl', port=443): Read timed out. (read timeout=30)

## zory

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-08 22:01 | 10 | biletyna.pl (5), zory.pl (5) |
| Gazeta | ✅ | 2026-11-08 22:01 | 14 | numery (14) |
| Wiadomości | ✅ | 2026-11-08 22:01 | 100 | IMGW (2), Radio 90 (30), zory.pl (68) |
| Godziny otwarcia | ✅ | 2026-11-08 22:01 | 10 | miejsca (10) |
| Punkty odpadów | ✅ | 2026-11-08 22:01 | 320 | punkty (1), słownik (319) |
| Transport | ❌ | 2026-10-26 04:43 | 187 | przystanki (187) |
| Odpady | ✅ | 2026-11-08 22:01 | 164 | rejony (164) |

Problemy:

- `transit/*` — 38× z rzędu od 2026-10-26T22:41: RuntimeError: no link matching 'GTFS(^/)*\\.zip$' on https://www.zory.pl/dla-mieszkancow/bezplatna-komunikacja-miejska

