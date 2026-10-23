# Status danych

Aktualizacja: 2026-10-23T05:10:00 (czas UTC runnera CI). Generowane przez `scraper/health.py` po każdym przebiegu; nie edytuj ręcznie.

Zgłoszenie na GitHubie otwiera się, gdy źródło zawiedzie 2 przebiegi z rzędu, i zamyka samo, gdy wróci.

## lubomia

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-10-23 04:46 | 20 | lubomia.pl (20) |
| Wiadomości | ✅ | 2026-10-23 04:46 | 73 | GOKSiR Lubomia (16), IMGW (1), Radio 90 (25), lubomia.pl (31) |
| Punkty odpadów | ✅ | 2026-10-23 04:46 | 60 | punkty (1), słownik (59) |
| Sport | ✅ | 2026-10-23 04:46 | 49 | naprzod-syrynia (17), silesia-lubomia (17), wypoczynek-bukow (15) |
| Transport | ✅ | 2026-10-23 04:46 | 93 | przystanki (93) |
| Odpady | ✅ | 2026-10-23 04:46 | 9 | rejony (9) |

## rybnik

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-10-23 04:47 | 125 | DK Boguszowice (15), DK Chwałowice (5), TZR (32), biletyna.pl (26), iRybnik (47) |
| Wiadomości | ✅ | 2026-10-23 04:47 | 120 | IMGW (1), Radio 90 (30), nowiny.pl (15), rybnik.com.pl (34), rybnik.eu (34), tuRybnik.pl (6) |
| Punkty odpadów | ✅ | 2026-10-23 04:47 | 62 | punkty (3), słownik (59) |
| Sport | ✅ | 2026-10-23 04:47 | 60 | row-1964 (36), row-kobiety (8), row-zuzel (16) |
| Transport | ❌ | 2026-10-22 04:42 | 626 | przystanki (626) |
| Odpady | ✅ | 2026-10-23 04:47 | 98 | rejony (98) |

Źródła zastępcze w użyciu (dane są, ale nie z głównego źródła):

- `news/rybnik.com.pl` przez `google_news` — główne: 403 Client Error: Forbidden for url: https://www.rybnik.com.pl/feed,feed0.html

Problemy:

- `transit/*` — 4× z rzędu od 2026-10-22T12:12: KeyError: "There is no item named 'shapes.txt' in the archive"

## zory

| Moduł | Stan | Ostatni sukces | Pozycji | Źródła (pozycji) |
|---|---|---|---|---|
| Wydarzenia | ✅ | 2026-10-22 21:34 | 8 | biletyna.pl (5), zory.pl (3) |
| Gazeta | ✅ | 2026-10-22 21:34 | 13 | numery (13) |
| Wiadomości | ✅ | 2026-10-22 21:34 | 88 | IMGW (1), Radio 90 (30), zory.pl (57) |
| Godziny otwarcia | ✅ | 2026-10-22 21:34 | 10 | miejsca (10) |
| Punkty odpadów | ✅ | 2026-10-22 21:34 | 320 | punkty (1), słownik (319) |
| Transport | ✅ | 2026-10-22 21:34 | 187 | przystanki (187) |
| Odpady | ✅ | 2026-10-22 21:34 | 164 | rejony (164) |

Problemy:

- `*/raport` — 1× z rzędu od 2026-10-23T05:10: miasto nie przysłało raportu w tym przebiegu (zadanie CI padło?)

