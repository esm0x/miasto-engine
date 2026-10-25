# Status danych

Aktualizacja: 2026-10-25T05:01:42 (czas UTC runnera CI). Generowane przez `scraper/health.py` po każdym przebiegu; nie edytuj ręcznie.

Zgłoszenie na GitHubie otwiera się, gdy źródło zawiedzie 2 przebiegi z rzędu, i zamyka samo, gdy wróci.

## lubomia

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-10-25 04:39 | 19 | lubomia.pl (19) |
| Wiadomości | ✅ | 2026-10-25 04:39 | 73 | GOKSiR Lubomia (16), IMGW (1), Radio 90 (25), lubomia.pl (31) |
| Punkty odpadów | ✅ | 2026-10-25 04:39 | 60 | punkty (1), słownik (59) |
| Sport | ✅ | 2026-10-25 04:39 | 49 | naprzod-syrynia (17), silesia-lubomia (17), wypoczynek-bukow (15) |
| Transport | ❌ | 2026-10-24 20:46 | 93 | przystanki (93) |
| Odpady | ✅ | 2026-10-25 04:39 | 9 | rejony (9) |

Problemy:

- `transit/*` — 1× z rzędu od 2026-10-25T05:01: ConnectTimeout: HTTPSConnectionPool(host='rozklady.powiatwodzislawski.pl', port=443): Max retries exceeded with url: / (Caused by ConnectTimeoutError(‹HTTPSConn

## rybnik

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-10-25 04:39 | 117 | DK Boguszowice (14), DK Chwałowice (5), TZR (34), biletyna.pl (29), iRybnik (35) |
| Wiadomości | ✅ | 2026-10-25 04:39 | 120 | IMGW (1), Radio 90 (30), nowiny.pl (15), rybnik.com.pl (35), rybnik.eu (33), tuRybnik.pl (6) |
| Punkty odpadów | ✅ | 2026-10-25 04:39 | 62 | punkty (3), słownik (59) |
| Sport | ✅ | 2026-10-25 04:39 | 60 | row-1964 (36), row-kobiety (8), row-zuzel (16) |
| Transport | ✅ | 2026-10-25 04:39 | 626 | przystanki (626) |
| Odpady | ✅ | 2026-10-25 04:39 | 98 | rejony (98) |

Źródła zastępcze w użyciu (dane są, ale nie z głównego źródła):

- `news/rybnik.com.pl` przez `google_news` — główne: 403 Client Error: Forbidden for url: https://www.rybnik.com.pl/feed,feed0.html

## zory

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-10-24 10:09 | 8 | biletyna.pl (5), zory.pl (3) |
| Gazeta | ✅ | 2026-10-24 10:09 | 13 | numery (13) |
| Wiadomości | ✅ | 2026-10-24 10:09 | 90 | IMGW (1), Radio 90 (30), zory.pl (59) |
| Godziny otwarcia | ✅ | 2026-10-24 10:09 | 10 | miejsca (10) |
| Punkty odpadów | ✅ | 2026-10-24 10:09 | 320 | punkty (1), słownik (319) |
| Transport | ✅ | 2026-10-24 10:09 | 187 | przystanki (187) |
| Odpady | ✅ | 2026-10-24 10:09 | 164 | rejony (164) |

Problemy:

- `*/raport` — 4× z rzędu od 2026-10-24T11:19: miasto nie przysłało raportu w tym przebiegu (zadanie CI padło?)

