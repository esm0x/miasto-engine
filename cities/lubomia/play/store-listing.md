# Opis do Google Play — Moja Lubomia

To nowa aplikacja w Play Console (**Utwórz aplikację**), a nie kolejne wydanie Mojego
Rybnika: inny pakiet, `com.adminstack.lubomia`. Gotowe teksty wklejasz w
**Grow → Store presence → Main store listing**.

---

## Nazwa aplikacji (max 30 znaków)

```
Moja Lubomia
```

*(12 znaków. To samo co `appName` w `cities/lubomia/city.json`, czyli nazwa pod ikoną.)*

---

## Krótki opis (max 80 znaków)

```
Odpady, autobusy, stan Odry, wydarzenia i komunikaty gminy. Bez reklam i kont.
```

*(78 znaków. Plik: `play/opis-krotki.txt`.)*

---

## Pełny opis (max 4000 znaków)

Wklej treść `play/opis-pelny.txt` (3797 znaków). Nie kopiuj go stąd ani z podglądu
z łamanymi wierszami, bo Play zachowuje każde złamanie wiersza.

Fakty z opisu sprawdzone na danych z 10 października 2026:
- 3 wodowskazy IMGW (Olza, Krzyżanowice, Racibórz-Miedonia), sprawdzanie co 3 h,
  powiadomienie po przekroczeniu stanu ostrzegawczego albo alarmowego,
- 5 linii powiatowych (31, 40, 41, 42, 44), 93 przystanki, kalendarz z dniami wolnymi i feriami,
- odpady: zmieszane, segregowane, bio, popiół, gabaryty, 5 rejonów,
- wiadomości: lubomia.pl, GOKSiR Lubomia, Radio 90, IMGW (powiat wodzisławski),
- PSZOK ul. Szkolna 4.

---

## Kategoria i kontakt

- **Kategoria aplikacji:** Wiadomości i czasopisma (jak Mój Rybnik)
- **Tagi:** wiadomości lokalne, transport publiczny, pogoda
- **E-mail kontaktowy:** office@admin-stack.com
- **Polityka prywatności:**
  `https://github.com/esm0x/miasto-engine/blob/main/cities/lubomia/PRIVACY.md`
- **Ikona i nazwa:** neutralna sylweta miasteczka, **bez herbu gminy** (herb wymaga
  pisemnej zgody rady gminy). W opisie stoi, że to projekt niezależny.

---

## Co nowego (pierwsze wydanie, max 500 znaków)

```
Pierwsze wydanie w Google Play.

Harmonogram odpadów dla każdej miejscowości gminy z przypomnieniem, stan Odry na żywo
z trzech wodowskazów IMGW z powiadomieniem o wezbraniu, rozkład linii powiatowych
z wyszukiwarką połączeń, wydarzenia, wiadomości z gminy i GOKSiR, ostrzeżenia IMGW,
jakość powietrza, wyłączenia prądu i słownik „gdzie wyrzucić” z PSZOK. Jasny i ciemny motyw.
```

---

## Zrzuty ekranu

Wszystkie w proporcjach 9:16, z podpisem w górnym pasie (18,75% wysokości, limit
Google to 20%), bez ramek urządzeń. Zrobione na emulatorach na wersji 0.1.0, z adresem
Syrynia, Wolności 7 i ulubionym przystankiem Lubomia, Mickiewicza Kościół. Przebudowa:
`python tools/store_assets.py lubomia` (surowe zrzuty w `screenshots-916/raw-*`,
podpisy w `play/captions.json`).

**Telefon:** `screenshots-916/phone/`, 1080 × 1920, w tej kolejności (pierwsze trzy
widać w wynikach wyszukiwania):

1. `01-start.png`: Najważniejsze na jednym ekranie
2. `02-odpady.png`: Wywóz odpadów pod Twój adres
3. `03-odra.png`: Stan Odry na żywo
4. `04-polaczenia.png`: Połączenia autobusowe
5. `05-wydarzenia.png`: Co się dzieje w gminie
6. `06-wiadomosci.png`: Wiadomości i komunikaty
7. `07-gdzie-wyrzucic.png`: Gdzie to wyrzucić?
8. `08-ciemny-motyw.png`: Jasny i ciemny motyw

**Tablet 7":** `screenshots-916/tablet-7/`, 1080 × 1920.
**Tablet 10":** `screenshots-916/tablet-10/`, 1440 × 2560.
Na tabletach po cztery: start, stan Odry, kalendarz wywozów, wydarzenia. Zamiast
odjazdów z przystanku jest stan Odry, bo wieczorem z Lubomi jadą już tylko jeden
albo dwa kursy i ekran odjazdów wychodzi prawie pusty.

## Grafiki

- `graphics/icon-512.png`: ikona 512 × 512, sylweta miasteczka na kolorze gminy
  (#2F6B3A), bez wewnętrznej ramki, bo Play sam zaokrągla rogi
- `graphics/feature-graphic-1024x500.png`: grafika promocyjna 1024 × 500
