# Status danych

Aktualizacja: 2026-11-15T06:26:15 (czas UTC runnera CI). Generowane przez `scraper/health.py` po każdym przebiegu; nie edytuj ręcznie.

Zgłoszenie na GitHubie otwiera się, gdy źródło zawiedzie 2 przebiegi z rzędu, i zamyka samo, gdy wróci.

## lubomia

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ❌ | 2026-11-15 06:25 | 17 |  |
| Wiadomości | ❌ | 2026-11-15 06:25 | 71 | GOKSiR Lubomia (17), IMGW (1), Radio 90 (22), lubomia.pl (31) |
| Punkty odpadów | ✅ | 2026-11-15 06:25 | 60 | punkty (1), słownik (59) |
| Sport | ✅ | 2026-11-15 06:25 | 49 | naprzod-syrynia (17), silesia-lubomia (17), wypoczynek-bukow (15) |
| Transport | ✅ | 2026-11-15 06:25 | 93 | przystanki (93) |
| Odpady | ❌ | 2026-11-14 06:17 | 9 | rejony (9) |

Problemy:

- `events/(pusto)` — 3× z rzędu od 2026-11-14T13:34: 0 pozycji, wcześniej 17
- `events/lubomia.pl` — 3× z rzędu od 2026-11-14T13:34: ConnectionError: HTTPSConnectionPool(host='lubomia.pl', port=443): Max retries exceeded with url: /wydarzenia/lista/2026/11 (Caused by NameResolutionError("HTTP
- `news/Sanepid Wodzisław` — 5× z rzędu od 2026-11-13T19:42: HTTPSConnectionPool(host='www.gov.pl', port=443): Max retries exceeded with url: /web/psse-wodzislaw-slaski/komunikaty (Caused by NewConnectionError("HTTPSConne
- `news/lubomia.pl/Aktualności` — 3× z rzędu od 2026-11-14T13:34: HTTPSConnectionPool(host='lubomia.pl', port=443): Max retries exceeded with url: /wiadomosci/kategoria/1 (Caused by NameResolutionError("HTTPSConnection(host='l
- `news/lubomia.pl/Ogłoszenia` — 3× z rzędu od 2026-11-14T13:34: HTTPSConnectionPool(host='lubomia.pl', port=443): Max retries exceeded with url: /wiadomosci/kategoria/4 (Caused by NameResolutionError("HTTPSConnection(host='l
- `waste/*` — 3× z rzędu od 2026-11-14T13:34: RuntimeError: waste: no rejony for 2026 (({'source': 'month_table_pdf', 'error': '2026: HTTPSConnectionPool(host=\'lubomia.pl\', port=443): Max retries exceeded

## rybnik

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-15 06:25 | 170 | DK Boguszowice (15), DK Chwałowice (5), TZR (22), biletyna.pl (40), iRybnik (88) |
| Wiadomości | ❌ | 2026-11-15 06:25 | 120 | IMGW (1), Radio 90 (30), nowiny.pl (15), rybnik.com.pl (35), rybnik.eu (34), tuRybnik.pl (5) |
| Punkty odpadów | ✅ | 2026-11-15 06:25 | 62 | punkty (3), słownik (59) |
| Sport | ✅ | 2026-11-15 06:25 | 60 | row-1964 (36), row-kobiety (8), row-zuzel (16) |
| Transport | ✅ | 2026-11-15 06:25 | 626 | przystanki (626) |
| Odpady | ✅ | 2026-11-15 06:25 | 98 | rejony (98) |

Źródła zastępcze w użyciu (dane są, ale nie z głównego źródła):

- `news/rybnik.com.pl` przez `google_news` — główne: 403 Client Error: Forbidden for url: https://www.rybnik.com.pl/feed,feed0.html

Problemy:

- `news/tuRybnik.pl` — 24× z rzędu od 2026-11-05T19:58: 403 Client Error: Forbidden for url: https://turybnik.pl/feed/

## zory

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-15 06:24 | 9 | biletyna.pl (5), zory.pl (4) |
| Gazeta | ✅ | 2026-11-15 06:24 | 14 | numery (14) |
| Wiadomości | ❌ | 2026-11-15 06:24 | 100 | IMGW (1), Radio 90 (30), zory.pl (69) |
| Godziny otwarcia | ✅ | 2026-11-15 06:24 | 10 | miejsca (10) |
| Punkty odpadów | ✅ | 2026-11-15 06:24 | 320 | punkty (1), słownik (319) |
| Transport | ❌ | 2026-10-26 04:43 | 187 | przystanki (187) |
| Odpady | ✅ | 2026-11-15 06:24 | 164 | rejony (164) |

Problemy:

- `news/Sanepid Rybnik` — 5× z rzędu od 2026-11-13T19:42: HTTPSConnectionPool(host='www.gov.pl', port=443): Max retries exceeded with url: /web/psse-rybnik/komunikaty (Caused by NewConnectionError("HTTPSConnection(host
- `transit/*` — 53× z rzędu od 2026-10-26T22:41: RuntimeError: no link matching 'GTFS(^/)*\\.zip$' on https://www.zory.pl/dla-mieszkancow/bezplatna-komunikacja-miejska

