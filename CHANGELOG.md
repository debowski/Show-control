# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/pl/1.1.0/).
Wersjonowanie: [Semantic Versioning](https://semver.org/lang/pl/).
Projekt jest przed 1.0 i nie ma zewnętrznych konsumentów API — zmiany widoczne
dla operatora idą jako patch, bo operator aktualizuje ręcznie i nie ma czego
łamać poza własnym przyzwyczajeniem.

## [Unreleased]

### Dodane

- `docs/refactor-plan.md` — plan podziału monolitu na pakiet `showcontrol/`,
  8 faz z bramami odbioru.
- `GLOSSARY.md` — terminy domenowe; „logo" wycofane na rzecz „overlay".
- `docs/adr/0001`–`0005` — pakiet z bootstrapem, overlay zamiast logo,
  Windows-only, fade 0–1 s, F9 nadpisuje overlay.
- `AGENTS.md`, `pyproject.toml` (ruff + pytest).
- Gałąź `refactor/plan`.

### Zmienione

- `GLOSSARY.md`, „Precedencja": F9 jest włącznikiem overlaya globalnego, nie
  nadpisaniem overlaya pozycji. Poprzednia wersja opisywała zamierzenie, nie
  kod. Ustalenie: `main.py:1746`, zgodnie z regułą z ADR 0002.
- `docs/refactor-plan.md` wzbogacony o przegląd architektury (sekcja 11):
  9 kandydatów przypisanych do istniejących faz, bez nowych faz.
- Dwa nowe defekty w sekcji 6: filtr dialogu „Dodaj pliki" (13) i overlay
  nieczyszczony przy wczytaniu projektu bez overlaya (14).

### Zmienione — planowane (faza 3, ADR 0005)

- **F9 nadpisuje overlay pozycji.** Przycisk zmienia nazwę na „Wymuś overlay",
  pokazuje overlay globalny i zasłania media oraz overlay bieżącej pozycji.
  Jest stanem do wyłączenia przez operatora, zerowanym przy starcie i przy
  wczytywaniu projektu. Przy braku assetu globalnego — wyszarzony.
- **Checkbox pozycji** znaczy wyłącznie „ta pozycja używa swojego overlaya";
  bez własnego assetu jest nieaktywny. Znika przypadek „użyj globalnego
  dla tej pozycji".
- **Migracja:** pozycje z `"overlay": true` i bez `overlay_path` tracą flagę
  przy wczytaniu, z jednorazowym komunikatem.

## [0.7.2] — planowane

Trzy commity przed rozpoczęciem refaktoru.

### Naprawione

- Brak `python-vlc` kończył się `NameError` zamiast komunikatu: `TRANSLATIONS`
  było używane w `main.py:28`, a definiowane w `main.py:40`.
- Etykieta fade'a pokazywała `2.0s` przy realnym czasie 0.8 s — `setValue(8)`
  wykonywało się przed podłączeniem `valueChanged`.

### Zmienione

- Zakres fade'a: **0–1.0 s** (było 0.2–2.0 s), domyślnie 0.8 s.
  Zmiana widoczna dla operatora, ale wydana jako patch — patrz nota na górze.
  Uzasadnienie: `docs/adr/0004-fade-0-1s.md`.

## [0.7.1] — 2026-11-13

Nowa linia bazowa. Wcześniejsze wydania nie tworzą ciągłej historii:
tagi `v0.3.9`–`v0.4.2` wskazują kod oznaczony w nagłówku jako `0.3.7`,
a `v0.3.5` i `v0.3.6` wskazują ten sam commit. Wersje 0.5 i 0.6 nie istnieją
w repozytorium — numeracja została przeskalowana bez odpowiednich wydań.

### Zmienione

- Przepisany README (funkcje, instalacja, build, troubleshooting).
- Nowy zrzut ekranu.
- Usunięty prototyp `test.py`.

### Uwagi

- `v0.4.2 → v0.7.1` to w kodzie 4 linie różnicy (dwie stałe wersji).
