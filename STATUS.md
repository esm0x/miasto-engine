# Status danych

Aktualizacja: 2026-10-16T11:43:35 (czas UTC runnera CI). Generowane przez `scraper/health.py` po każdym przebiegu; nie edytuj ręcznie.

Zgłoszenie na GitHubie otwiera się, gdy źródło zawiedzie 2 przebiegi z rzędu, i zamyka samo, gdy wróci.

## lubomia

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-10-16 11:20 | 20 | lubomia.pl (20) |
| Wiadomości | ✅ | 2026-10-16 11:20 | 73 | GOKSiR Lubomia (16), IMGW (1), Radio 90 (25), lubomia.pl (31) |
| Punkty odpadów | ✅ | 2026-10-16 11:20 | 60 | punkty (1), słownik (59) |
| Sport | ✅ | 2026-10-16 11:20 | 49 | naprzod-syrynia (17), silesia-lubomia (17), wypoczynek-bukow (15) |
| Transport | ✅ | 2026-10-16 11:20 | 93 | przystanki (93) |
| Odpady | ✅ | 2026-10-16 11:20 | 9 | rejony (9) |

## rybnik

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-10-16 11:23 | 135 | DK Boguszowice (17), DK Chwałowice (7), TZR (33), biletyna.pl (25), iRybnik (53) |
| Wiadomości | ⚠️ | 2026-10-16 11:23 | 120 | IMGW (1), Radio 90 (30), nowiny.pl (15), rybnik.com.pl (34), rybnik.eu (34), tuRybnik.pl (6) |
| Punkty odpadów | ✅ | 2026-10-16 11:23 | 62 | punkty (3), słownik (59) |
| Sport | ✅ | 2026-10-16 11:23 | 60 | row-1964 (36), row-kobiety (8), row-zuzel (16) |
| Transport | ✅ | 2026-10-16 11:23 | 626 | przystanki (626) |
| Odpady | ✅ | 2026-10-16 11:23 | 98 | rejony (98) |

Źródła zastępcze w użyciu (dane są, ale nie z głównego źródła):

- `news/rybnik.com.pl` przez `google_news` — główne: 403 Client Error: Forbidden for url: https://www.rybnik.com.pl/feed,feed0.html

Problemy:

- `news/IMGW` — 1× z rzędu od 2026-10-16T11:43: HTTPSConnectionPool(host='danepubliczne.imgw.pl', port=443): Max retries exceeded with url: /api/data/warningsmeteo (Caused by NameResolutionError("HTTPSConnect

## zory

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-10-15 21:21 | 8 | biletyna.pl (5), zory.pl (3) |
| Gazeta | ✅ | 2026-10-15 21:21 | 13 | numery (13) |
| Wiadomości | ✅ | 2026-10-15 21:21 | 71 | IMGW (1), Radio 90 (30), zory.pl (40) |
| Godziny otwarcia | ✅ | 2026-10-15 21:21 | 10 | miejsca (10) |
| Punkty odpadów | ✅ | 2026-10-15 21:21 | 320 | punkty (1), słownik (319) |
| Transport | ✅ | 2026-10-15 21:21 | 187 | przystanki (187) |
| Odpady | ✅ | 2026-10-15 21:21 | 164 | rejony (164) |

Problemy:

- `*/raport` — 2× z rzędu od 2026-10-16T04:52: miasto nie przysłało raportu w tym przebiegu (zadanie CI padło?)

