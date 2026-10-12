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

Flavor powstaje sam z katalogu. **Ikona musi być własna:** domyślna sylweta miasteczka
z `app/src/main` to tylko zaślepka na czas zakładania miasta. Na pasku stanu ikona
powiadomień jest białą maską, więc dwa miasta na jednej sylwecie są nie do odróżnienia;
`CityConfigTest` nie przepuści drugiego miasta z tym samym kształtem. Narysuj prosty glif
z lokalnym motywem (Żory: tężnia z fontanną, Lubomia: gród nad Odrą) i połóż go jako
`app/src/<slug>/res/drawable/ic_city_glyph.xml` (108 dp, w kole 66 dp, evenOdd) oraz
przycięty jako `ic_notification.xml` (24 dp). Ten sam glif daje ikonę monochromatyczną
Androida 13+ i ikonę do sklepu (`tools/store_assets.py`). Sprawdź go w 24 px: drobne
szczegóły znikają. Gotowa grafika (jak Rybnik) idzie do `mipmap-*`.
**Herbu ani logo promocyjnego miasta nie używaj bez pisemnej zgody** (`pomysły/06-prawo-i-ryzyka.md`).

Na emulatorze przejdź: Start, wybór adresu (każdy rodzaj: wieś w całości, ulica),
Śmieci, Wydarzenia, Więcej → Gdzie wyrzucić, Ustawienia. Moduły wyłączone nie mogą
się nigdzie pokazać.

## 5. Sklep

- `cities/<slug>/play/` — opisy i zrzuty (wzór: `cities/lubomia/play/`)
- surowe zrzuty 9:16 z emulatorów do `play/screenshots-916/raw-phone`, `raw-tablet7`,
  `raw-tablet10` (telefon 1080×1920, tablet 7" 1080×1920 @280 dpi, tablet 10" 1440×2560
  @320 dpi); pasek statusu czyścić trybem demo Androida, broadcast z `-f 0x10000000`
  (bez tej flagi SystemUI na tabletach potrafi się zawiesić)
- godzina na zrzutach ma sens: urząd otwarty, autobusy kursują. Bez roota zegara nie
  przestawisz, ale strefę tak: `adb shell cmd alarm set-timezone America/New_York`
  (wieczorem w Polsce daje przedpołudnie), dopiero po pełnym starcie systemu, i zegar
  trybu demo ustaw na faktyczną godzinę urządzenia (`date +%H%M`), bo apka liczy „otwarte
  do…” według zegara, nie paska. Skrypty: `tools/qa/` (wzór Żor) albo jak w Lubomii
- emulatory po jednym naraz i z `-memory 2048`: przy 16 GB RAM, Android Studio
  i demonach Gradle dwa emulatory potrafią zawiesić gościa (`./gradlew --stop` pomaga)
- podpisy w `play/captions.json`, potem `python tools/store_assets.py <slug>`:
  zrzuty z podpisami w kolorach miasta, `graphics/icon-512.png` (sylweta miasteczka)
  i `graphics/feature-graphic-1024x500.png`; skrypt sprawdza limity Google Play
- polityka prywatności: `cities/rybnik/PRIVACY.md` jako wzór, z domenami tego miasta
- `./gradlew bundle<Slug>Release`, podpis tym samym keystore'em co Rybnik

## 6. Utrzymanie

Przy N miastach źródła psują się co kilka dni (`pomysły/03-architektura-multi-miasto.md`,
„Koszt utrzymania”). Alarmy już są: źródło martwe 2 przebiegi z rzędu = zgłoszenie na
GitHubie i mail, stan wszystkich w `STATUS.md`. Zostaje zasada: **nowe miasto dopiero
po 14 dniach zielonego `STATUS.md` dla poprzednich.**

Źródło odpadów musi przyjmować parametr `year` i rzucać `NotPublished`, gdy gmina nie
wydała jeszcze harmonogramu na ten rok (wzór: `month_table_pdf.py`). Rok wybiera moduł.
