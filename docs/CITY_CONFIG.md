# Konfiguracja miasta

Dwa pliki w `cities/<slug>/`. `slug` to małe litery i cyfry (`lubomia`, `zory`), równy
nazwie katalogu — Gradle i testy sprawdzają to przy każdym buildzie.

## city.json — tożsamość (czyta Gradle i apka)

| Pole | Przykład | Uwagi |
|---|---|---|
| `slug` | `"lubomia"` | = nazwa katalogu i flavora |
| `name` | `"Lubomia"` | nagłówek Startu |
| `locative` | `"w gminie Lubomia"` | „PM10 … µg/m³ w gminie Lubomia” |
| `appName` | `"Moja Lubomia"` | nazwa pod ikoną i w ustawieniach powiadomień |
| `android.applicationId` | `"com.adminstack.lubomia"` | **nieodwracalny** po publikacji |
| `android.versionCode` / `versionName` | `1` / `"0.1.0"` | osobno dla każdego miasta |
| `dataBaseUrl` | `"https://raw.githubusercontent.com/esm0x/miasto-engine/main/data/lubomia/"` | musi kończyć się `/<slug>/` |
| `contactEmail` | `"office@admin-stack.com"` | ekran Kontakt |
| `repoUrl`, `donateUrl` | `null` | `null` ukrywa przyciski GitHuba i „Postaw kawę” |
| `modules` | `{"transit": false, "sport": false}` | domyślnie wszystko włączone; wypisz tylko braki |
| `theme` | `{"primary": "#2F6B3A", …}` | 8 kolorów `#RRGGBB`; brakujące = paleta Rybnika. `primary` to też tło domyślnej ikony |
| `air.stationId`, `air.stationName` | `845`, `"Wodzisław Śląski, ul. Gałczyńskiego"` | stacja GIOŚ z PM10 — patrz niżej |
| `outages.cityGaids` | `{"*": 13}` albo `{"Lubomia": 1636, "Syrynia": 1638}` | Tauron: jedno id dla miasta albo osobne na każdą wieś (klucz = dzielnica z harmonogramu) |
| `transit.operatorName`, `downloadSizeLabel`, `ignoredRoutes` | `"KM Rybnik"`, `"ok. 0,6 MB"`, `["-->"]` | tylko gdy jest GTFS |
| `waste.districtPickTitle` | `"Wybierz miejscowość"` | pierwszy krok wyboru adresu |
| `waste.addressHint` | | pod pustym ekranem odpadów |
| `waste.houseTypeHint` | | tylko gdy gmina dzieli harmonogram na domy/bloki |
| `waste.destinationHints` | `{"INNE": "sprawdź na lubomia.pl"}` | podpowiedzi w „gdzie wyrzucić”, np. adres GPZON |
| `dataSources` | `"Gmina Lubomia (odpady, …), GIOŚ (…)"` | „Dane: …” w Ustawieniach (mianownik) |
| `dataCredit` | `"Gminy Lubomia, GIOŚ, IMGW i Tauron Dystrybucja"` | „Dane pochodzą od …” (dopełniacz) |
| `authorityGenitive` | `"gminy"` | „nie jest oficjalnym produktem gminy” |
| `sportSummary` | `"ROW 1964, żużel, piłka kobiet"` | podpis wiersza Sport |

Jak znaleźć parametry, które trzeba sprawdzić w źródle (nie zgadywać):

```bash
# GIOŚ: najbliższe stacje i czy mają PM10
curl -s "https://api.gios.gov.pl/pjp-api/v1/rest/station/findAll?size=500"
curl -s "https://api.gios.gov.pl/pjp-api/v1/rest/station/sensors/845"
# Tauron: id miejscowości (filtruj po gminie — nazwy się powtarzają w całej Polsce)
curl -s "https://www.tauron-dystrybucja.pl/waapi/enum/geo/cities?partName=Syrynia"
```

TERYT powiatu do IMGW (4 cyfry, np. `2415` = wodzisławski) — z rejestru TERYT GUS.

## sources.json — skąd dane (czytają tylko scrapery)

Klucze najwyższego poziomu to moduły: `events`, `news`, `sport`, `points`, `transit`,
`waste`. Każde źródło ma `type` = plik w `scraper/sources/<moduł>/<type>.py`; reszta pól
to jego parametry, opisane w docstringu tego pliku.

### Parsery wielokrotnego użytku (pierwszy wybór dla nowego miasta)

| Moduł | `type` | Dla kogo |
|---|---|---|
| events | `idcom` | gminy na portalu IDcom CMS-GOV (`cms-v2-files.idcom-jst.pl` w adresach obrazków) |
| events | `wp_ical` | WordPress + The Events Calendar (`?ical=1`) — większość domów kultury |
| events | `biletyna` | `https://biletyna.pl/<Miasto>` |
| events | `manual` | `cities/<slug>/manual_events.json` — Facebook, plakaty, telefon od sołtysa |
| news | `rss` | każdy kanał RSS (Radio 90 ma tag na miasto: `/tag/<miasto>/feed`) |
| news | `idcom` | aktualności i ogłoszenia z portalu IDcom |
| news | `imgw` | ostrzeżenia IMGW po TERYT powiatu — działa wszędzie |
| sport | `minut90` | klub piłkarski z 90minut.pl (`clubId`) |
| sport | `ekstraliga` | klub żużlowy (Ekstraliga, 1. i 2. liga) |
| points | `manual` | `cities/<slug>/points.json` |
| waste | `month_table_pdf` | PDF z tabelą na rejon: wiersze = frakcje, kolumny = miesiące |

### Parsery tylko dla Rybnika

`tzr`, `irybnik`, `row_speedway` (events), `typo3_rybnik_eu` (news), `rybnik_eu` (points),
`rybnik_eu_pdf` (waste), `km_rybnik` (transit). Wzór, jak pisać źródło pod konkretną
stronę, gdy nic z listy wyżej nie pasuje.

### Ustawienia modułów

- `events.venues` — `[["regex", "Nazwa miejsca"], …]`: rozpoznawanie miejsc w opisach
- `events.cityWords` — odmiana nazwy miasta, ignorowana przy porównywaniu tytułów
- `events.extraCategoryRules` — `[["Festiwal", "kiermasz|festyn"], …]`, sprawdzane
  *po* wspólnych regułach (uzupełniają, nie nadpisują)
- `events.clubVenues`, `events.sourceRank` — patrz Rybnik
- `news.maxItems`, `news.maxAgeDays`, `news.extraAlertKeywords`, `cap` na źródle
- `points.guide` — nazwa pliku słownika „gdzie wyrzucić” w katalogu miasta
