# Status danych

Aktualizacja: 2026-11-02T15:46:56 (czas UTC runnera CI). Generowane przez `scraper/health.py` po każdym przebiegu; nie edytuj ręcznie.

Zgłoszenie na GitHubie otwiera się, gdy źródło zawiedzie 2 przebiegi z rzędu, i zamyka samo, gdy wróci.

## lubomia

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-02 15:44 | 19 | lubomia.pl (19) |
| Wiadomości | ✅ | 2026-11-02 15:44 | 72 | GOKSiR Lubomia (17), IMGW (1), Radio 90 (23), lubomia.pl (31) |
| Punkty odpadów | ✅ | 2026-11-02 15:44 | 60 | punkty (1), słownik (59) |
| Sport | ✅ | 2026-11-02 15:44 | 49 | naprzod-syrynia (17), silesia-lubomia (17), wypoczynek-bukow (15) |
| Transport | ✅ | 2026-11-02 15:44 | 93 | przystanki (93) |
| Odpady | ✅ | 2026-11-02 15:44 | 9 | rejony (9) |

## rybnik

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-02 15:46 | 118 | DK Boguszowice (15), DK Chwałowice (6), TZR (34), biletyna.pl (21), iRybnik (42) |
| Wiadomości | ✅ | 2026-11-02 15:46 | 120 | IMGW (1), Radio 90 (30), nowiny.pl (15), rybnik.com.pl (35), rybnik.eu (33), tuRybnik.pl (6) |
| Punkty odpadów | ✅ | 2026-11-02 15:46 | 62 | punkty (3), słownik (59) |
| Sport | ✅ | 2026-11-02 15:46 | 60 | row-1964 (36), row-kobiety (8), row-zuzel (16) |
| Transport | ✅ | 2026-11-02 15:46 | 626 | przystanki (626) |
| Odpady | ✅ | 2026-11-02 15:46 | 98 | rejony (98) |

Źródła zastępcze w użyciu (dane są, ale nie z głównego źródła):

- `news/rybnik.com.pl` przez `google_news` — główne: 403 Client Error: Forbidden for url: https://www.rybnik.com.pl/feed,feed0.html

## zory

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-02 15:44 | 6 | biletyna.pl (5), zory.pl (1) |
| Gazeta | ✅ | 2026-11-02 15:44 | 13 | numery (13) |
| Wiadomości | ✅ | 2026-11-02 15:44 | 100 | IMGW (1), Radio 90 (30), zory.pl (69) |
| Godziny otwarcia | ✅ | 2026-11-02 15:44 | 10 | miejsca (10) |
| Punkty odpadów | ✅ | 2026-11-02 15:44 | 320 | punkty (1), słownik (319) |
| Transport | ❌ | 2026-10-26 04:43 | 187 | przystanki (187) |
| Odpady | ✅ | 2026-11-02 15:44 | 164 | rejony (164) |

Problemy:

- `transit/*` — 22× z rzędu od 2026-10-26T22:41: RuntimeError: no link matching 'GTFS(^/)*\\.zip$' on https://www.zory.pl/dla-mieszkancow/bezplatna-komunikacja-miejska

