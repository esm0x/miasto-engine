# Nowe miasto — krok po kroku

Tak powstała Lubomia (10.10.2026). Realny koszt gminy wiejskiej na IDcom bez autobusów:
jeden dzień, z czego większość to sprawdzanie danych.

## 0. Wycena danych (zanim cokolwiek napiszesz)

Przejdź `pomysły/szablony/checklista-nowe-miasto.md`, sekcja 0. Najważniejsze pytania:
w jakiej formie jest harmonogram odpadów (Excel / PDF z tabelą / skan), na jakim silniku
stoi strona gminy (IDcom? WordPress?), czy jest GTFS, czy to teren Tauronu.

**Konkurencja:** sprawdź na stronie gminy, czy nie poleca EcoHarmonogramu albo BLISKO
(patrz `pomysły/14-pszczyna-rozeznanie.md`).

## 1. Katalog miasta

```bash
mkdir cities/<slug>
cp cities/lubomia/city.json cities/lubomia/sources.json cities/<slug>/
mkdir data/<slug> && echo {} > data/<slug>/announcement.json
```

Wypełnij `city.json` według [CITY_CONFIG.md](CITY_CONFIG.md). Każdy identyfikator
(stacja GIOŚ, Tauron, TERYT) sprawdź w API, nie zgaduj — w Rybniku pierwsze trafienie
dla nazwy „Rybnik” w Tauronie to wieś w łódzkim.

## 2. Źródła

W `sources.json` zacznij od parserów wielokrotnego użytku (tabela w CITY_CONFIG.md).
Jeśli harmonogram ma inny układ niż którykolwiek parser — napisz nowy w
`scraper/sources/waste/`, wzorując się na `month_table_pdf.py`. Zwraca listę rejonów
w kształcie z `scraper/CONTRACT.md`; wieś bez ulic dostaje ulicę `"*"`.

Pliki ręczne: `manual_events.json` (szablon w Lubomii), `points.json` (PSZOK),
`waste_guide.json` — skopiuj z Lubomii lub Rybnika i **popraw to, co lokalne**
(czy jest GPZON, co przyjmuje PSZOK, jak odbierane są gabaryty).

```bash
python scraper/build.py --city <slug>
```

Moduł, który łamie kontrakt, nic nie zapisze i powie dlaczego.

## 3. Weryfikacja — nie do pominięcia

Brak błędu ≠ dobre dane. Dla Lubomii:

- harmonogram porównany z niezależnym parsowaniem i z surową tabelą PDF (data w datę),
- każde wydarzenie przejrzane z kategorią i miejscem,
- wiadomości przejrzane pod kątem treści z innych miast (feedy regionalne!).

Minimum: **10 adresów z różnych miejscowości/dzielnic porównanych z PDF-em gminy.**

## 4. Apka

```bash
./gradlew testLubomiaDebugUnitTest     # CityConfigTest sprawdza też nowy city.json
./gradlew assemble<Slug>Debug
```

Flavor powstaje sam z katalogu. Ikona: domyślna sylweta miasteczka w kolorze `primary`.
Własną ikonę wrzuć do `app/src/<slug>/res/` (mipmap-*, `drawable/ic_notification.xml`).
**Herbu gminy nie używaj bez pisemnej zgody** (`pomysły/06-prawo-i-ryzyka.md`).

Na emulatorze przejdź: Start, wybór adresu (każdy rodzaj: wieś w całości, ulica),
Śmieci, Wydarzenia, Więcej → Gdzie wyrzucić, Ustawienia. Moduły wyłączone nie mogą
się nigdzie pokazać.

## 5. Sklep

- `cities/<slug>/play/` — opisy i zrzuty (wzór: `cities/lubomia/play/`)
- surowe zrzuty 9:16 z emulatorów do `play/screenshots-916/raw-phone`, `raw-tablet7`,
  `raw-tablet10` (telefon 1080×1920, tablet 7" 1080×1920 @280 dpi, tablet 10" 1440×2560
  @320 dpi); pasek statusu czyścić trybem demo Androida, broadcast z `-f 0x10000000`
  (bez tej flagi SystemUI na tabletach potrafi się zawiesić)
- podpisy w `play/captions.json`, potem `python tools/store_assets.py <slug>`:
  zrzuty z podpisami w kolorach miasta, `graphics/icon-512.png` (sylweta miasteczka)
  i `graphics/feature-graphic-1024x500.png`; skrypt sprawdza limity Google Play
- polityka prywatności: `cities/rybnik/PRIVACY.md` jako wzór, z domenami tego miasta
- `./gradlew bundle<Slug>Release`, podpis tym samym keystore'em co Rybnik

## 6. Utrzymanie

Przy N miastach źródła psują się co kilka dni (`pomysły/03-architektura-multi-miasto.md`,
„Koszt utrzymania”). Zanim dołożysz trzecie miasto: alert z CI przy `failures`
dwa przebiegi z rzędu i zasada „nowe miasto dopiero po 14 dniach zielonego CI”.
