# 🚉 Testy Kolejowe
Aplikacja webowa przeznaczona do przeprowadzania testów wiedzy zawodowej dla pracowników kolei (maszynistów, kierowników pociągu, dyżurnych ruchu), oparta na instrukcjach Ir-1 oraz Ie-1. System pozwala na zarządzanie bazą pytań, obsługę grafik oraz automatyczne wyliczanie statystyk zdawalności.

## 🚀 Główne Funkcje
Trzy poziomy uprawnień:

* Administrator: Zarządzanie użytkownikami, grupami zawodowymi i strukturą testów.
* Edytor: Pełne zarządzanie bazą pytań (CRUD) wraz z dodawaniem grafik i komentarzy merytorycznych.
* Użytkownik: Rozwiązywanie testów przypisanych do danej grupy zawodowej.

Inteligentny system losowania: Losowanie 30 pytań z puli (z powtórzeniami, jeśli baza jest mniejsza lub unikalnie, jeśli jest większa).

Mobilna optymalizacja: Interfejs dostosowany do telefonów i tabletów.

Statystyki: Automatyczne monitorowanie "współczynnika zdawalności" dla każdego pytania.

Bezpieczeństwo: Szyfrowanie haseł (Bcrypt) i pełna konteneryzacja.

## 🛠️ Architektura i Technologie
* Frontend/Backend: Python + Streamlit (serwer wbudowany)
* Baza danych: MariaDB 10.11
* ORM: SQLAlchemy
* Konteneryzacja: Docker & Docker Compose
* Proxy: Wsparcie dla Nginx Proxy Manager (SSL Let's Encrypt)

## 📦 Wdrożenie (Deployment)
1. Klonowanie repozytorium
Bash
git clone https://github.com/twoj-uzytkownik/testy-kolejowe.git
cd testy-kolejowe
2. Konfiguracja sieci (Ważne!)
Aplikacja została zaprojektowana do działania obok stacku Lizmap. Aby kontenery mogły się komunikować z Nginx Proxy Managerem, muszą znajdować się w tej samej sieci.

[!IMPORTANT] Przed uruchomieniem sprawdź nazwę swojej sieci zewnętrznej:

```Bash
docker network ls
```
Jeśli Twoja sieć Lizmap nazywa się inaczej niż lizmap-dc-ssl_default, zaktualizuj ją w pliku docker-compose.yml w sekcji networks -> web -> name.

3. Uruchomienie
```Bash
docker compose up -d --build
```
Aplikacja będzie dostępna lokalnie pod adresem http://localhost:8501.

## 💾 Backup i Konserwacja
Wszystkie dane są mapowane bezpośrednio na dysk serwera (Bind Mounts), co ułatwia ich kopiowanie:

Baza danych: ./db_data

Grafiki pytań: ./uploads

W katalogu znajduje się skrypt backup.sh, który tworzy skompresowane archiwum bazy i plików.

## 👥 Autorzy
SQ9NIT & AJ

Rok powstania: 2026

Stworzone z dużą ilością kawy.

## 📝 Plik .dockerignore i .gitignore
Pamiętaj, aby nie wysyłać na GitHub katalogów db_data/, uploads/ oraz venv/. Są one wykluczone w dołączonych plikach konfiguracyjnych.