# Status danych

Aktualizacja: 2026-11-14T13:34:22 (czas UTC runnera CI). Generowane przez `scraper/health.py` po każdym przebiegu; nie edytuj ręcznie.

Zgłoszenie na GitHubie otwiera się, gdy źródło zawiedzie 2 przebiegi z rzędu, i zamyka samo, gdy wróci.

## lubomia

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ⚠️ | 2026-11-14 13:33 | 17 |  |
| Wiadomości | ❌ | 2026-11-14 13:33 | 71 | GOKSiR Lubomia (17), IMGW (1), Radio 90 (22), lubomia.pl (31) |
| Punkty odpadów | ✅ | 2026-11-14 13:33 | 60 | punkty (1), słownik (59) |
| Sport | ✅ | 2026-11-14 13:33 | 49 | naprzod-syrynia (17), silesia-lubomia (17), wypoczynek-bukow (15) |
| Transport | ✅ | 2026-11-14 13:33 | 93 | przystanki (93) |
| Odpady | ❌ | 2026-11-14 06:17 | 9 | rejony (9) |

Problemy:

- `events/(pusto)` — 1× z rzędu od 2026-11-14T13:34: 0 pozycji, wcześniej 17
- `events/lubomia.pl` — 1× z rzędu od 2026-11-14T13:34: ConnectionError: HTTPSConnectionPool(host='lubomia.pl', port=443): Max retries exceeded with url: /wydarzenia/lista/2026/11 (Caused by NameResolutionError("HTTP
- `news/Sanepid Wodzisław` — 3× z rzędu od 2026-11-13T19:42: HTTPSConnectionPool(host='www.gov.pl', port=443): Max retries exceeded with url: /web/psse-wodzislaw-slaski/komunikaty (Caused by NewConnectionError("HTTPSConne
- `news/lubomia.pl/Aktualności` — 1× z rzędu od 2026-11-14T13:34: HTTPSConnectionPool(host='lubomia.pl', port=443): Max retries exceeded with url: /wiadomosci/kategoria/1 (Caused by NameResolutionError("HTTPSConnection(host='l
- `news/lubomia.pl/Ogłoszenia` — 1× z rzędu od 2026-11-14T13:34: HTTPSConnectionPool(host='lubomia.pl', port=443): Max retries exceeded with url: /wiadomosci/kategoria/4 (Caused by NameResolutionError("HTTPSConnection(host='l
- `waste/*` — 1× z rzędu od 2026-11-14T13:34: RuntimeError: waste: no rejony for 2026 (({'source': 'month_table_pdf', 'error': '2026: HTTPSConnectionPool(host=\'lubomia.pl\', port=443): Max retries exceeded

## rybnik

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-14 13:34 | 165 | DK Boguszowice (15), DK Chwałowice (4), TZR (28), biletyna.pl (19), iRybnik (99) |
| Wiadomości | ❌ | 2026-11-14 13:34 | 120 | IMGW (1), Radio 90 (30), nowiny.pl (16), rybnik.com.pl (34), rybnik.eu (34), tuRybnik.pl (5) |
| Punkty odpadów | ✅ | 2026-11-14 13:34 | 62 | punkty (3), słownik (59) |
| Sport | ✅ | 2026-11-14 13:34 | 60 | row-1964 (36), row-kobiety (8), row-zuzel (16) |
| Transport | ✅ | 2026-11-14 13:34 | 626 | przystanki (626) |
| Odpady | ✅ | 2026-11-14 13:34 | 98 | rejony (98) |

Źródła zastępcze w użyciu (dane są, ale nie z głównego źródła):

- `news/rybnik.com.pl` przez `google_news` — główne: 403 Client Error: Forbidden for url: https://www.rybnik.com.pl/feed,feed0.html

Problemy:

- `news/tuRybnik.pl` — 22× z rzędu od 2026-11-05T19:58: 403 Client Error: Forbidden for url: https://turybnik.pl/feed/

## zory

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-14 13:33 | 10 | biletyna.pl (5), zory.pl (5) |
| Gazeta | ✅ | 2026-11-14 13:33 | 14 | numery (14) |
| Wiadomości | ❌ | 2026-11-14 13:33 | 100 | IMGW (1), Radio 90 (30), zory.pl (69) |
| Godziny otwarcia | ✅ | 2026-11-14 13:33 | 10 | miejsca (10) |
| Punkty odpadów | ✅ | 2026-11-14 13:33 | 320 | punkty (1), słownik (319) |
| Transport | ❌ | 2026-10-26 04:43 | 187 | przystanki (187) |
| Odpady | ✅ | 2026-11-14 13:33 | 164 | rejony (164) |

Problemy:

- `news/Sanepid Rybnik` — 3× z rzędu od 2026-11-13T19:42: HTTPSConnectionPool(host='www.gov.pl', port=443): Max retries exceeded with url: /web/psse-rybnik/komunikaty (Caused by NewConnectionError("HTTPSConnection(host
- `transit/*` — 51× z rzędu od 2026-10-26T22:41: RuntimeError: no link matching 'GTFS(^/)*\\.zip$' on https://www.zory.pl/dla-mieszkancow/bezplatna-komunikacja-miejska

