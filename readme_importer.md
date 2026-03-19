# 📥 Instrukcja Importera Pytań (v2.0 - Marzec 2026)

System obsługuje masowy import pytań wraz z dokumentacją zdjęciową. 

### 1. Przygotowanie plików
Aby import zakończył się sukcesem, musisz przygotować dwa pliki:
1. **Arkusz Excel (.xlsx):** Zawierający treść pytań, odpowiedzi i nazwy plików graficznych.
2. **Archiwum ZIP (.zip):** Zawierające wszystkie obrazy wymienione w Excelu.

### 2. Struktura Arkusza Excel
Każdy wiersz to jedno pytanie. Kolumny muszą nazywać się dokładnie tak:
* `content` - Treść pytania.
* `ans_a`, `ans_b`, `ans_c` - Teksty odpowiedzi.
* `correct_ans` - Litera poprawnej odpowiedzi (A, B lub C).
* `profession_names` - Nazwy grup zawodowych rozdzielone przecinkiem (np. `Maszynista, Kierownik pociągu`).
* `test_types` - Kategorie testu rozdzielone przecinkiem (np. `Tabor, Ruch`).
* `image_q` - Nazwa pliku obrazka dla pytania (np. `semafor_1.png`).
* `image_a`, `image_b`, `image_c` - Nazwy obrazków dla odpowiedzi (opcjonalnie).

### 3. Procedura Importu
1. Zaloguj się na konto Administratora.
2. Przejdź do zakładki **Panel Administracyjny -> Import**.
3. Wgraj plik `.xlsx`. System sprawdzi poprawność nagłówków.
4. Wgraj plik `.zip`. System zweryfikuje, czy wszystkie nazwy z Excela znajdują się w archiwum.
5. Kliknij **"Synchronizuj bazę"**.

> ⚠️ **Uwaga:** Jeśli pytanie o danej treści już istnieje, system zaktualizuje jego metadane zamiast tworzyć duplikat.