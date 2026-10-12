# Opis do Google Play: Moje Żory

To nowa aplikacja w Play Console (**Utwórz aplikację**), a nie kolejne wydanie Mojego
Rybnika: inny pakiet, `com.adminstack.zory`. Gotowe teksty wklejasz w
**Grow → Store presence → Main store listing**.

> **Zanim wydasz:** 26.08.2026 miasto uruchomiło oficjalną aplikację **mMieszkaniec**
> (Rekord Mobile: ogłoszenia, zgłoszenia, odpady, mapa atrakcji, cyfrowa karta
> mieszkańca). Moje Żory jej nie udaje i nie powtarza nazwy, ale w sklepie będą obok
> siebie. Czym się różnimy: bezpłatne autobusy BKM z rozkładem offline i wyszukiwarką
> połączeń, „co dziś otwarte” z rezerwacją wizyty w urzędzie, kiosk Kuriera Żorskiego,
> harmonogram dla bloków co do budynku, powietrze, wyłączenia prądu, widget.

---

## Nazwa aplikacji (max 30 znaków)

```
Moje Żory
```

*(9 znaków. To samo co `appName` w `cities/zory/city.json`.)*

---

## Krótki opis (max 80 znaków)

```
Odpady, darmowe autobusy BKM, co dziś otwarte, Kurier Żorski. Bez reklam i kont.
```

*(80 znaków. Plik: `play/opis-krotki.txt`.)*

---

## Pełny opis (max 4000 znaków)

Wklej treść `play/opis-pelny.txt` (3921 znaków). Nie kopiuj go stąd ani z podglądu
z łamanymi wierszami, bo Play zachowuje każde złamanie wiersza.

Fakty z opisu sprawdzone na danych z 11-12 października 2026:
- odpady: PDF dla domów (16 rejonów + 29 odcinków „utrudnionych”) i 10 plików Word dla
  bloków (119 grup budynków); frakcje: zmieszane, bio, zielone, popiół, papier/plastik/szkło,
  gabaryty, elektronika, opony, liście i choinki; próbki porównane z plikami miasta,
- BKM: 9 linii, 187 przystanków, GTFS miasta ważny do 31.12.2026 (nowe wydanie dociąga
  się samo),
- co dziś otwarte: urząd, PSZOK i 8 atrakcji z godzinami przepisanymi ze stron miasta,
  strony pilnowane skrótem, zmiana = alarm w `STATUS.md`,
- Kurier Żorski: 13 numerów z 2025-2026, okładki i PDF ze strony miasta,
- słownik „gdzie wyrzucić”: 319 haseł z żorskiego alfabetu odpadów,
- powietrze: stacja GIOŚ w Jastrzębiu-Zdroju (stacja w Żorach mierzy pył tylko ręcznie,
  wyniki są po 4-8 tygodniach),
- wiadomości: zory.pl, Radio 90, PSSE Rybnik, IMGW (powiat żorski).

---

## Kategoria i kontakt

- **Kategoria aplikacji:** Wiadomości i czasopisma (jak Mój Rybnik)
- **Tagi:** wiadomości lokalne, transport publiczny
- **E-mail kontaktowy:** office@admin-stack.com
- **Polityka prywatności:**
  `https://github.com/esm0x/miasto-engine/blob/main/cities/zory/PRIVACY.md`
- **Ikona i nazwa:** neutralna sylweta miasteczka w kolorze #B23A1E, **bez herbu ani logo
  miasta** (herb wymaga zgody rady miasta). W opisie stoi, że to projekt niezależny.

---

## Wydanie w Play Console

- **Plik:** `app/build/outputs/bundle/zoryRelease/app-zory-release.aab`
  (`./gradlew bundleZoryRelease`), podpisany tym samym kluczem co Mój Rybnik
- **Wersja:** 1.0.0, versionCode 1
- **Nazwa wydania:** `1 (1.0.0)`
- **Co nowego** (max 500 znaków): wklej `play/co-nowego-1.0.0.txt` (354 znaki).

---

## Zrzuty ekranu

Wszystkie w proporcjach 9:16, z podpisem w górnym pasie (18,75% wysokości, limit
Google to 20%), bez ramek urządzeń. Zrobione na emulatorach 12.10.2026 na wersji 1.0.0,
z adresem Wodzisławska 218 (dom) i ulubionym przystankiem Centrum Przesiadkowe, w
poniedziałek przed południem (strefa czasowa emulatora przestawiona, żeby urząd i
autobusy były w godzinach pracy). Przebudowa: `python tools/store_assets.py zory`.

Kurier Żorski celowo nie ma osobnego zrzutu: okładki to logo i zdjęcia miasta, a zrzut
w sklepie nie powinien sugerować, że aplikacja jest miejska. Kurier jest widoczny jako
karta na ekranie startowym.

**Telefon:** `screenshots-916/phone/`, 1080 × 1920:

1. `01-start.png`: Najważniejsze na jednym ekranie
2. `02-odpady.png`: Wywóz odpadów pod Twój adres
3. `03-co-otwarte.png`: Co dziś otwarte
4. `04-autobusy.png`: Bezpłatne autobusy BKM
5. `05-wydarzenia.png`: Co się dzieje w Żorach
6. `06-wiadomosci.png`: Wiadomości i komunikaty
7. `07-gdzie-wyrzucic.png`: Gdzie to wyrzucić?
8. `08-ciemny-motyw.png`: Jasny i ciemny motyw

**Tablet 7":** `screenshots-916/tablet-7/`, 1080 × 1920.
**Tablet 10":** `screenshots-916/tablet-10/`, 1440 × 2560.
Na tabletach po cztery: start, co dziś otwarte, kalendarz wywozów, wydarzenia.

## Grafiki

- `graphics/icon-512.png`: ikona 512 × 512, sylweta miasteczka na kolorze #B23A1E
- `graphics/feature-graphic-1024x500.png`: grafika promocyjna 1024 × 500
