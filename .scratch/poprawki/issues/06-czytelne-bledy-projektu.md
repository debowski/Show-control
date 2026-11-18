# 06: Czytelne błędy pliku projektu

**What to build:** Zepsuty lub niepełny plik projektu daje zrozumiały komunikat
(„nieprawidłowy plik projektu") ze wskazaniem, czego brakuje lub co jest
nie tak, zamiast surowego wyjątku w oknie. Błąd zapisu — np. brak uprawnień —
też mówi po ludzku. Operator nie traci przy tym dotychczasowej playlisty.

**Blocked by:** None (can start immediately)

**Status:** ready-for-human

- [x] Uszkodzony JSON daje komunikat po ludzku, nie surowy wyjątek
- [x] Brak wymaganego pola lub zły typ daje wskazanie, które pole jest błędne
- [x] Błąd zapisu (brak uprawnień, zajęty plik) daje czytelny komunikat
- [x] Po nieudanym wczytaniu dotychczasowa playlista zostaje nietknięta

## Comments

Realizacja: `domain/project_schema.py` ma `ProjectFileError` — wyjątek
z nazwą problemu (`key`) i szczegółami (`params`: pole, indeks, typ JSON)
oraz `validate_project_data`, które sprawdza kształt danych przed konwersją.
Wymagane jest pole `files` (lista); każda pozycja to tekst (legacy) albo obiekt
z tekstowym `path`; `overlay`, `overlay_path` i globalny overlay muszą mieć
właściwe typy. `project_from_data` nadal jest tolerancyjny dla starych plików
i migracji ADR 0005 — walidacja dotyczy wejścia z pliku.

`persistence/project_io.py` zamienia `JSONDecodeError` na `ProjectFileError`
z linią i kolumną oraz `UnicodeDecodeError` na komunikat o kodowaniu. Błędy
systemowe (brak pliku, uprawnienia) zostają `OSError`, bo nie dotyczą treści.

`window.py`: `ProjectFileError` daje okno „Nieprawidłowy plik projektu”
z tłumaczonym szczegółem (`project_error_*` w PL/EN), a `OSError` — powód
po ludzku: brak uprawnień, plik używany przez inny program (WinError 32/33),
brak pliku/katalogu, brak miejsca. Zapis używa tych samych powodów. Cały
odczyt, walidacja i podział pozycji dzieją się **przed** wyczyszczeniem
playlisty, więc nieudane wczytanie nie zmienia bieżącej listy, overlaya ani
`last_project`.

Weryfikacja: `pytest` — 119 zielonych (nowe testy walidacji i błędów odczytu),
`python -m ruff check .` czysto. Smoke headless na prawdziwym `MainWindow`:
uszkodzony JSON, złe `files`, brak `path` — playlista i `last_project`
nietknięte, komunikat zawiera linię/pole; poprawny projekt nadal się wczytuje;
`PermissionError` przy zapisie daje „Brak uprawnień do pliku.”. `python main.py`
w trybie offscreen startuje i działa. Do potwierdzenia na sprzęcie: dialog
z prawdziwym plikiem zablokowanym przez inny program oraz brakujące
uprawnienia w systemie plików.
