# Status danych

Aktualizacja: 2026-11-24T00:00:25 (czas UTC runnera CI). Generowane przez `scraper/health.py` po każdym przebiegu; nie edytuj ręcznie.

Zgłoszenie na GitHubie otwiera się, gdy źródło zawiedzie 2 przebiegi z rzędu, i zamyka samo, gdy wróci.

## lubomia

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-23 23:53 | 17 | lubomia.pl (17) |
| Wiadomości | ⚠️ | 2026-11-23 23:53 | 71 | GOKSiR Lubomia (16), IMGW (1), Radio 90 (23), lubomia.pl (31) |
| Punkty odpadów | ✅ | 2026-11-23 23:53 | 60 | punkty (1), słownik (59) |
| Sport | ✅ | 2026-11-23 23:53 | 49 | naprzod-syrynia (17), silesia-lubomia (17), wypoczynek-bukow (15) |
| Transport | ✅ | 2026-11-23 23:53 | 93 | przystanki (93) |
| Odpady | ✅ | 2026-11-23 23:53 | 9 | rejony (9) |

Problemy:

- `news/Sanepid Wodzisław` — 1× z rzędu od 2026-11-24T00:00: HTTPSConnectionPool(host='www.gov.pl', port=443): Max retries exceeded with url: /web/psse-wodzislaw-slaski/komunikaty (Caused by NewConnectionError("HTTPSConne

## rybnik

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-24 00:00 | 152 | DK Boguszowice (14), DK Chwałowice (4), TZR (27), biletyna.pl (51), iRybnik (56) |
| Wiadomości | ❌ | 2026-11-24 00:00 | 120 | IMGW (1), Radio 90 (28), nowiny.pl (15), rybnik.com.pl (43), rybnik.eu (28), tuRybnik.pl (5) |
| Punkty odpadów | ⚠️ | 2026-11-24 00:00 | 59 | punkty (0), słownik (59) |
| Sport | ✅ | 2026-11-24 00:00 | 60 | row-1964 (36), row-kobiety (8), row-zuzel (16) |
| Transport | ✅ | 2026-11-24 00:00 | 622 | przystanki (622) |
| Odpady | ❌ | 2026-11-23 07:33 | 98 | rejony (98) |

Problemy:

- `news/rybnik.eu/dla-mieszkancow/aktualnosci` — 1× z rzędu od 2026-11-24T00:00: HTTPSConnectionPool(host='www.rybnik.eu', port=443): Max retries exceeded with url: /dla-mieszkancow/aktualnosci (Caused by ConnectTimeoutError(‹HTTPSConnection
- `news/rybnik.eu/dla-mieszkancow/aktualnosci/kategoria/inwestycje` — 1× z rzędu od 2026-11-24T00:00: HTTPSConnectionPool(host='www.rybnik.eu', port=443): Max retries exceeded with url: /dla-mieszkancow/aktualnosci/kategoria/inwestycje (Caused by ConnectTimeoutE
- `news/rybnik.eu/dla-mieszkancow/aktualnosci/kategoria/komunikacja` — 1× z rzędu od 2026-11-24T00:00: HTTPSConnectionPool(host='www.rybnik.eu', port=443): Max retries exceeded with url: /dla-mieszkancow/aktualnosci/kategoria/komunikacja (Caused by ConnectTimeout
- `news/rybnik.eu/dla-mieszkancow/aktualnosci/kategoria/komunikaty` — 1× z rzędu od 2026-11-24T00:00: HTTPSConnectionPool(host='www.rybnik.eu', port=443): Max retries exceeded with url: /dla-mieszkancow/aktualnosci/kategoria/komunikaty (Caused by ConnectTimeoutE
- `news/tuRybnik.pl` — 41× z rzędu od 2026-11-05T19:58: 403 Client Error: Forbidden for url: https://turybnik.pl/feed/
- `points/GPZON` — 1× z rzędu od 2026-11-24T00:00: HTTPSConnectionPool(host='www.rybnik.eu', port=443): Max retries exceeded with url: /dla-mieszkancow/odpady-komunalne/odpady-niebezpieczne-gpzon (Caused by Conn
- `points/PSZOK` — 1× z rzędu od 2026-11-24T00:00: HTTPSConnectionPool(host='www.rybnik.eu', port=443): Max retries exceeded with url: /dla-mieszkancow/odpady-komunalne/punkty-zbiorki-odpadow-pszok (Caused by Co
- `waste/*` — 1× z rzędu od 2026-11-24T00:00: RuntimeError: waste: no rejony for 2026 (({'source': 'rybnik_eu_pdf', 'error': "2026: HTTPSConnectionPool(host='www.rybnik.eu', port=443): Max retries exceeded 

## zory

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-11-23 23:52 | 10 | biletyna.pl (5), zory.pl (5) |
| Gazeta | ✅ | 2026-11-23 23:52 | 14 | numery (14) |
| Wiadomości | ⚠️ | 2026-11-23 23:52 | 100 | IMGW (1), Radio 90 (30), zory.pl (69) |
| Godziny otwarcia | ✅ | 2026-11-23 23:52 | 10 | miejsca (10) |
| Punkty odpadów | ✅ | 2026-11-23 23:52 | 320 | punkty (1), słownik (319) |
| Transport | ❌ | 2026-10-26 04:43 | 187 | przystanki (187) |
| Odpady | ✅ | 2026-11-23 23:52 | 164 | rejony (164) |

Problemy:

- `news/Sanepid Rybnik` — 1× z rzędu od 2026-11-24T00:00: HTTPSConnectionPool(host='www.gov.pl', port=443): Max retries exceeded with url: /web/psse-rybnik/komunikaty (Caused by NewConnectionError("HTTPSConnection(host
- `transit/*` — 70× z rzędu od 2026-10-26T22:41: RuntimeError: no link matching 'GTFS(^/)*\\.zip$' on https://www.zory.pl/dla-mieszkancow/bezplatna-komunikacja-miejska

