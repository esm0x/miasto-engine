# Polityka prywatności: Moje Żory

Obowiązuje od 12 października 2026. Dotyczy aplikacji Android **Moje Żory**
(identyfikator pakietu `com.adminstack.zory`).

## Krótko

Aplikacja **nie zbiera żadnych danych o użytkowniku**, nie zakłada kont, nie ma reklam
ani narzędzi analitycznych. Nie ma serwera, na który cokolwiek by wysyłała. Wszystko,
co ustawisz, zostaje na Twoim telefonie.

## Jakie dane przechowuje aplikacja

Wyłącznie lokalnie, w pamięci aplikacji na Twoim urządzeniu:

- **adres do harmonogramu odpadów** (ulica, numer domu, rodzaj zabudowy): podajesz go sam,
  służy do wybrania właściwego rejonu wywozu i do sprawdzania wyłączeń prądu pod tym
  adresem,
- **ulubione wydarzenia i przystanki**,
- **ustawienia powiadomień** (które włączone, próg alertu smogowego, godzina
  przypomnienia o wywozie),
- **ukryte komunikaty** (identyfikatory wiadomości, które sam schowałeś),
- **wybrany motyw** (jasny / ciemny / jak system),
- **pobrane dane publiczne** w pamięci podręcznej (wydarzenia, wiadomości, harmonogram
  odpadów, rozkład jazdy), żeby aplikacja działała bez internetu.

Odinstalowanie aplikacji usuwa je wszystkie. Wyczyszczenie danych aplikacji
w ustawieniach systemu daje ten sam efekt.

**Jeden wyjątek: wyłączenia prądu.** Żeby sprawdzić wyłączenia pod Twoim adresem,
aplikacja musi zapytać o niego serwis Tauron Dystrybucja, wysyła więc **miasto,
nazwę ulicy i numer domu** do `www.tauron-dystrybucja.pl`. Bez tego ta funkcja nie
zadziała. Nie wysyłamy przy tym Twojego imienia, identyfikatora urządzenia ani niczego
innego, a my sami nie otrzymujemy tych danych: nie mamy żadnego serwera. Jeśli nie
chcesz, żeby adres wychodził z telefonu, wyłącz powiadomienia o wyłączeniach prądu
w Ustawieniach i nie otwieraj tej sekcji.

## Z czym aplikacja łączy się przez internet

Aplikacja pobiera publicznie dostępne dane. Poza opisanym wyżej przypadkiem wyłączeń
prądu nie wysyła Twojego adresu, identyfikatora urządzenia ani niczego, co pozwalałoby
Cię rozpoznać. W szczególności harmonogram odpadów jest filtrowany **wyłącznie na
telefonie**: pobieramy komplet rejonów i dopasowanie do Twojego adresu odbywa się
lokalnie.

| Dokąd | Po co |
|---|---|
| `raw.githubusercontent.com` | wydarzenia, wiadomości, harmonogram odpadów, PSZOK, godziny otwarcia, lista numerów Kuriera Żorskiego, rozkład jazdy BKM (kopia pliku GTFS publikowanego przez miasto) |
| `www.zory.pl` | okładki numerów Kuriera Żorskiego (miniatury obrazków ze strony miasta) |
| `api.gios.gov.pl` | jakość powietrza, stacja Jastrzębie-Zdrój (GIOŚ) |
| `www.tauron-dystrybucja.pl` | wyłączenia prądu; **tu trafia miasto, ulica i numer domu** |

Standardowo, jak przy każdym połączeniu internetowym, serwery te widzą adres IP
Twojego urządzenia. Nie mamy na to wpływu i nie mamy do tych logów dostępu.

Linki do stron źródłowych (np. zory.pl, numery Kuriera Żorskiego w PDF, miejski system
rezerwacji wizyt bezkolejki.zory.pl) oraz do buycoffee.to i GitHuba otwierają się w Twojej przeglądarce
dopiero po kliknięciu. Co dzieje się dalej, określają zasady tych serwisów.

## Uprawnienia

- **Internet**: pobieranie danych opisanych wyżej.
- **Powiadomienia**: przypomnienia o wywozie odpadów, ulubionych wydarzeniach,
  przekroczeniu progu smogu, komunikatach miasta, nowym numerze Kuriera Żorskiego
  i wyłączeniach prądu. Możesz odmówić, a aplikacja działa dalej, tylko bez
  powiadomień.
- **Uruchamianie po starcie systemu**: odtworzenie zaplanowanych przypomnień po
  restarcie telefonu.

Aplikacja **nie prosi o dostęp** do lokalizacji, kontaktów, aparatu, mikrofonu,
plików ani kalendarza.

## Dzieci

Aplikacja nie jest kierowana do dzieci i nie zbiera danych od nikogo, niezależnie
od wieku.

## Źródła danych i zastrzeżenie

Dane pochodzą od: Miasta Żory, Instytutu Meteorologii i Gospodarki Wodnej, Głównego
Inspektoratu Ochrony Środowiska, Powiatowej Stacji Sanitarno-Epidemiologicznej
w Rybniku, Tauron Dystrybucja, Radia 90 i serwisów biletowych.

**Aplikacja jest projektem niezależnym i nie jest oficjalnym produktem Miasta Żory
ani żadnej z wymienionych instytucji.** Dane prezentujemy w dobrej wierze, ale nie
gwarantujemy ich poprawności ani aktualności. W sprawach urzędowych zawsze sprawdzaj
źródło i kieruj się komunikatami miasta i służb.

## Zmiany

Zmiany w tej polityce będą publikowane pod tym samym adresem, wraz z nową datą
obowiązywania.

## Kontakt

office@admin-stack.com
