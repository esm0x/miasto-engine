# Status danych

Aktualizacja: 2026-10-22T12:12:04 (czas UTC runnera CI). Generowane przez `scraper/health.py` po każdym przebiegu; nie edytuj ręcznie.

Zgłoszenie na GitHubie otwiera się, gdy źródło zawiedzie 2 przebiegi z rzędu, i zamyka samo, gdy wróci.

## lubomia

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-10-22 11:48 | 20 | lubomia.pl (20) |
| Wiadomości | ✅ | 2026-10-22 11:48 | 73 | GOKSiR Lubomia (16), IMGW (1), Radio 90 (25), lubomia.pl (31) |
| Punkty odpadów | ✅ | 2026-10-22 11:48 | 60 | punkty (1), słownik (59) |
| Sport | ✅ | 2026-10-22 11:48 | 49 | naprzod-syrynia (17), silesia-lubomia (17), wypoczynek-bukow (15) |
| Transport | ✅ | 2026-10-22 11:48 | 93 | przystanki (93) |
| Odpady | ✅ | 2026-10-22 11:48 | 9 | rejony (9) |

## rybnik

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-10-22 11:51 | 115 | DK Boguszowice (15), DK Chwałowice (9), TZR (32), biletyna.pl (14), iRybnik (45) |
| Wiadomości | ✅ | 2026-10-22 11:51 | 120 | IMGW (1), Radio 90 (30), nowiny.pl (16), rybnik.com.pl (33), rybnik.eu (34), tuRybnik.pl (6) |
| Punkty odpadów | ✅ | 2026-10-22 11:51 | 62 | punkty (3), słownik (59) |
| Sport | ✅ | 2026-10-22 11:51 | 60 | row-1964 (36), row-kobiety (8), row-zuzel (16) |
| Transport | ❌ | 2026-10-22 04:42 | 626 | przystanki (626) |
| Odpady | ✅ | 2026-10-22 11:51 | 98 | rejony (98) |

Źródła zastępcze w użyciu (dane są, ale nie z głównego źródła):

- `news/rybnik.com.pl` przez `google_news` — główne: 403 Client Error: Forbidden for url: https://www.rybnik.com.pl/feed,feed0.html

Problemy:

- `transit/*` — 1× z rzędu od 2026-10-22T12:12: KeyError: "There is no item named 'shapes.txt' in the archive"

## zory

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ❌ | 2026-10-22 05:02 | 5 | biletyna.pl (5) |
| Gazeta | ❌ | 2026-10-21 11:45 | 13 | numery (13) |
| Wiadomości | ❌ | 2026-10-22 05:02 | 87 | IMGW (1), Radio 90 (30), zory.pl (56) |
| Godziny otwarcia | ❌ | 2026-10-22 05:02 | 10 | miejsca (10) |
| Punkty odpadów | ✅ | 2026-10-22 05:02 | 320 | punkty (1), słownik (319) |
| Transport | ❌ | 2026-10-21 11:45 | 187 | przystanki (187) |
| Odpady | ❌ | 2026-10-21 11:45 | 164 | rejony (164) |

Problemy:

- `*/raport` — 1× z rzędu od 2026-10-22T12:12: miasto nie przysłało raportu w tym przebiegu (zadanie CI padło?)
- `events/zory.pl` — 3× z rzędu od 2026-10-21T17:33: ConnectTimeout: HTTPSConnectionPool(host='www.zory.pl', port=443): Max retries exceeded with url: /json/ (Caused by ConnectTimeoutError(‹HTTPSConnection(host='w
- `gazette/*` — 3× z rzędu od 2026-10-21T17:33: RuntimeError: gazette: no issues found (({'source': 'https://www.zory.pl/', 'error': "HTTPSConnectionPool(host='www.zory.pl', port=443): Max retries exceeded wi
- `news/zory.pl/dla-mieszkancow/aktualnosci` — 3× z rzędu od 2026-10-21T17:33: HTTPSConnectionPool(host='www.zory.pl', port=443): Max retries exceeded with url: /dla-mieszkancow/aktualnosci (Caused by NameResolutionError("HTTPSConnection(h
- `news/zory.pl/dla-mieszkancow/eko-zory/aktualnosci` — 3× z rzędu od 2026-10-21T17:33: HTTPSConnectionPool(host='www.zory.pl', port=443): Max retries exceeded with url: /dla-mieszkancow/eko-zory/aktualnosci (Caused by ConnectTimeoutError(‹HTTPSCon
- `news/zory.pl/dla-mieszkancow/gospodarka-odpadami/aktualnosci` — 3× z rzędu od 2026-10-21T17:33: HTTPSConnectionPool(host='www.zory.pl', port=443): Max retries exceeded with url: /dla-mieszkancow/gospodarka-odpadami/aktualnosci (Caused by NameResolutionErro
- `places/aquarion` — 3× z rzędu od 2026-10-21T17:33: nie da się sprawdzić https://www.zory.pl/strefa-turysty/amerykanski-park-rozrywki-twinpigs-4-1-2: HTTPSConnectionPool(host='www.zory.pl', port=443): Max retries
- `places/fontanna-rynek` — 2× z rzędu od 2026-10-21T22:02: nie da się sprawdzić https://www.zory.pl/strefa-turysty/amerykanski-park-rozrywki-twinpigs-4-1: HTTPSConnectionPool(host='www.zory.pl', port=443): Max retries e
- `places/karuzela-zorzanka` — 2× z rzędu od 2026-10-21T22:02: nie da się sprawdzić https://www.zory.pl/strefa-turysty/amerykanski-park-rozrywki-twinpigs-4: HTTPSConnectionPool(host='www.zory.pl', port=443): Max retries exc
- `places/muzeum-ognia` — 3× z rzędu od 2026-10-21T17:33: nie da się sprawdzić https://www.zory.pl/strefa-turysty/amerykanski-park-rozrywki-twinpigs-4-1-1: HTTPSConnectionPool(host='www.zory.pl', port=443): Max retries
- `places/palac-baranowice` — 3× z rzędu od 2026-10-21T17:33: nie da się sprawdzić https://www.zory.pl/strefa-turysty/amerykanski-park-rozrywki-twinpigs-3: HTTPSConnectionPool(host='www.zory.pl', port=443): Max retries exc
- `places/pszok` — 3× z rzędu od 2026-10-21T17:33: nie da się sprawdzić https://www.zory.pl/dla-mieszkancow/gospodarka-odpadami/pszok: HTTPSConnectionPool(host='www.zory.pl', port=443): Max retries exceeded with
- `places/rajska-fala` — 2× z rzędu od 2026-10-21T22:02: nie da się sprawdzić https://www.zory.pl/strefa-turysty/amerykanski-park-rozrywki-twinpigs-2: HTTPSConnectionPool(host='www.zory.pl', port=443): Max retries exc
- `places/teznia` — 3× z rzędu od 2026-10-21T17:33: nie da się sprawdzić https://www.zory.pl/strefa-turysty/amerykanski-park-rozrywki-twinpigs-1: HTTPSConnectionPool(host='www.zory.pl', port=443): Max retries exc
- `places/twinpigs` — 2× z rzędu od 2026-10-21T22:02: nie da się sprawdzić https://www.zory.pl/strefa-turysty/amerykanski-park-rozrywki-twinpigs-4-1-3: HTTPSConnectionPool(host='www.zory.pl', port=443): Max retries
- `places/urzad-miasta` — 3× z rzędu od 2026-10-21T17:33: nie da się sprawdzić https://www.zory.pl/dla-mieszkancow/internetowy-system-kolejkowy: HTTPSConnectionPool(host='www.zory.pl', port=443): Max retries exceeded w
- `transit/*` — 3× z rzędu od 2026-10-21T17:33: ConnectTimeout: HTTPSConnectionPool(host='www.zory.pl', port=443): Max retries exceeded with url: /dla-mieszkancow/bezplatna-komunikacja-miejska (Caused by Conn
- `waste/*` — 3× z rzędu od 2026-10-21T17:33: RuntimeError: waste: no rejony for 2026 (({'source': 'zory_typo3', 'error': "2026: HTTPSConnectionPool(host='www.zory.pl', port=443): Max retries exceeded with 

