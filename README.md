# Miasto Engine — aplikacje miejskie z jednego kodu

Jeden kod Androida i jeden zestaw scraperów, z których powstaje osobna aplikacja dla
każdej gminy: własna nazwa w sklepie, własny identyfikator, kolory i dane. Wyrosło
z [Mój Rybnik](docs/RYBNIK.md) (1.3.1), którego historia, decyzje i 20+ pułapek
w danych są w `docs/RYBNIK.md` — warto je przeczytać przed pierwszym nowym miastem.

| Miasto | Apka | Moduły | Stan |
|---|---|---|---|
| `rybnik` | Mój Rybnik, `com.adminstack.rybnik` | wszystkie | wydana (1.3.1 z `rybnik-app`); scrapowana **tylko tutaj**, następne wydania z tego repo |
| `lubomia` | Moja Lubomia, `com.adminstack.lubomia` | wydarzenia, wiadomości, odpady, punkty, powietrze, prąd | demo, niewydana |

## Jak to jest poskładane

```
cities/<slug>/city.json        tożsamość miasta: nazwa, applicationId, wersja, kolory,
                               moduły, stacja GIOŚ, Tauron, teksty. Czyta go Gradle
                               (robi z niego flavor) i apka (z assets).
cities/<slug>/sources.json     skąd scrapery biorą dane: które parsery, z jakimi
                               parametrami. Moduł, którego nie ma w pliku, nie istnieje.
cities/<slug>/*.json           pliki edytowane ręcznie: manual_events, waste_guide, points
cities/<slug>/play/            grafiki i opisy do Sklepu Play (Rybnik)

data/<slug>/*.json             wynik scraperów — to pobiera apka. Tu też announcement.json.

app/src/main/                  wspólny kod apki (pakiet com.adminstack.miasto)
app/src/<slug>/                tylko to, czego nie da się opisać w JSON: ikony, a dla
                               Rybnika aliasy starych nazw klas (patrz niżej)

scraper/build.py               python scraper/build.py --city lubomia
scraper/engine/                wspólne: HTTP, tekst, kontekst, walidacja kontraktu
scraper/modules/               co robi moduł dla każdego miasta (dedupe, alerty, …)
scraper/sources/<moduł>/       parsery konkretnych źródeł, wybierane przez "type"
scraper/CONTRACT.md            format JSON-ów — wiążący dla apki
```

Zasada: **flavor i kod nie zawierają `if (miasto == …)`.** Jeśli nowe miasto czegoś
takiego potrzebuje, brakuje pola w `city.json`. Jedynym wyjątkiem są parsery w
`scraper/sources/`, bo każda gmina publikuje dane inaczej — ale też tam lepiej pisać
parser pod *silnik strony* (IDcom, WordPress + The Events Calendar, TYPO3) niż pod gminę.

## Na co dzień

```bash
pip install -r scraper/requirements.txt
python scraper/build.py --list                     # miasta i ich moduły
python scraper/build.py --city lubomia             # wszystkie moduły jednego miasta
python scraper/build.py --city rybnik --only news  # jeden moduł
```

Apka (JDK 21, patrz `docs/RYBNIK.md`):

```bash
./gradlew assembleLubomiaDebug                     # debug jednego miasta
./gradlew bundleRybnikRelease                      # AAB do sklepu
./gradlew testRybnikDebugUnitTest                  # testy (sprawdzają też każdy city.json)
```

CI (`.github/workflows/scrape.yml`) co 6 h buduje dane wszystkich miast — każde miasto
to osobne zadanie, więc padnięte źródło w jednym nie blokuje innych — i robi jeden
commit. Harmonogramy odpadów przelicza tylko przy pushu albo ręcznym uruchomieniu.

## Nowe miasto

Krok po kroku: **[docs/NOWE-MIASTO.md](docs/NOWE-MIASTO.md)**. Pola konfiguracji:
**[docs/CITY_CONFIG.md](docs/CITY_CONFIG.md)**.

## Rzeczy, o których trzeba pamiętać

- **`applicationId` jest nieodwracalny.** Po pierwszej publikacji nie wolno go zmienić —
  test `CityConfigTest` pilnuje, żeby Rybnik został `com.adminstack.rybnik`.
- **Jeden keystore dla wszystkich miast** (`keystore.properties` poza repo), z Play App
  Signing. Kopia keystore'a w dwóch miejscach offline.
- **Komentarze w `app/build.gradle.kts`:** w Kotlinie komentarze blokowe się zagnieżdżają,
  więc ścieżka z ukośnikiem i gwiazdką (jak glob) w komentarzu po cichu wyłącza resztę
  skryptu. Tak raz zniknęło kopiowanie `city.json` i APK uruchamiałby się bez konfiguracji.
- **Rybnik a `rybnik-app`:** Rybnik jest scrapowany wyłącznie tutaj. `rybnik-app` nie scrapuje,
  tylko co godzinę kopiuje `data/rybnik/*.json` do swojego `scraper/data/`, bo stamtąd czytają
  zainstalowane wersje 1.3.x. Dlatego **ogłoszenie dla Rybnika edytujesz tutaj**
  (`data/rybnik/announcement.json`); trafi też do starych wersji. Kopię można wyłączyć, gdy
  w statystykach Play nie będzie już instalacji 1.3.x.
- **Wydanie Rybnika z silnika:** flavor `rybnik` ma aliasy starych nazw
  (`com.adminstack.rybnik.MainActivity` dla ikony, `…rybnik.widget.WasteWidgetReceiver`
  dla postawionych widgetów) i ten sam plik ustawień (`rybnik_prefs`). Sprawdzone na
  emulatorze: aktualizacja 1.2.7 → wersja z silnika zachowała adres, ikonę i harmonogram.
  Następne wydanie: `./gradlew bundleRybnikRelease` z versionCode > 19 (teraz 20 w `city.json`),
  ten sam keystore; `keystore.properties` trzeba skopiować z `rybnik-app` (jest w `.gitignore`).
- **Dane muszą być publiczne** pod `dataBaseUrl` — raw.githubusercontent.com nie podaje
  plików z prywatnych repo. Jeśli kod ma być prywatny, dane trzeba publikować osobno
  (np. osobne publiczne repo albo Cloudflare Pages) i zmienić `dataBaseUrl`.
