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
- `tests/` — testy domeny, ustawień, motywu i zapisu/odczytu projektu.
  Bez Qt i VLC, `pytest` w CI-lokalnym zakresie.

### Zmienione

- Monolit `main.py` rozbity na pakiet `showcontrol/`: `bootstrap.py` tworzy
  jedno `QApplication` i jedno `QSettings`, `ui/theme.py` i `ui/i18n.py` to
  przeniesienie 1:1, `domain/` (media, playlista, reguły overlaya, schemat
  projektu) nie importuje Qt ani VLC. `main.py` to 8-liniowy bootstrap.
- `playback/engine.py` przejmuje `vlc.Instance`, dwa odtwarzacze, `set_hwnd`,
  głośność, jasność i wyciszenie overlaya. Usunięte gałęzie
  `sys.platform.startswith("win")` — zostaje ścieżka Windows.
- Zapis i odczyt projektu korzystają z `domain/project_schema.py` zamiast
  sięgać po `PlaylistModel._data`. Format JSON bez zmian.
- `playback/session.py` przejmuje transport, autoplay, polling 500 ms i strażnik
  przejścia. `App` traci `is_playing`, `is_transitioning`, `user_is_seeking`
  i `_current_media_path()`. `playing_row` przechodzi z `PlaylistStore` do
  sesji; model dostaje wyłącznie wskaźnik do narysowania. Czyste reguły
  przesunięcia indeksu przy zmianach wierszy zostają w `domain/playlist.py`.
  `SessionState` + sygnał `failure` są seamem recovery dla fazy B.
- `playback/fade.py` — `FadeController` przejmuje stan fade i kroki wygaszania.
- `playback/overlay.py` — jeden kontroler ładowania assetu i trybu projekcji;
  zniknęły dwa rozjechane bloki `_load_overlay_media` / `update_logo_media`
  i dwa wskaźniki „aktualnie załadowanego assetu".
- Nazwy `logo` → `overlay` w kodzie i UI (`OverlayViewer`, `set_mode_overlay`,
  `overlay_on_audio_checkbox`, `force_overlay_btn`). Odczyt projektu nadal
  przyjmuje stary klucz `"logo"`, ale zapis używa wyłącznie `"overlay"`.
- `GLOSSARY.md`, „Precedencja": F9 jest włącznikiem overlaya globalnego, nie
  nadpisaniem overlaya pozycji. Poprzednia wersja opisywała zamierzenie, nie
  kod. Ustalenie: `main.py:1746`, zgodnie z regułą z ADR 0002.
- `docs/refactor-plan.md` wzbogacony o przegląd architektury (sekcja 11):
  9 kandydatów przypisanych do istniejących faz, bez nowych faz.
- Dwa nowe defekty w sekcji 6: filtr dialogu „Dodaj pliki" (13) i overlay
  nieczyszczony przy wczytaniu projektu bez overlaya (14).

### Zmienione — faza 5

- `ui/layout.py` buduje trzy panele operatora; `window.py` spina moduły
  i nie zawiera logiki VLC.
- Jedna tabela `ui/shortcuts.py` niesie klucz, akcję i etykietę. Zniknęły
  `KEY_TOOLTIP_LABELS` i drugie źródło opisów skrótów.
- `apply_translations` używa stabilnych identyfikatorów zamiast rozpoznawania
  widżetów po treści; teksty spoza systemu trafiły do `ui/i18n.py`.
- Delegate, lista i etykiety paneli czytają tokeny motywu; `list_play` ma
  konsumenta.

### Zmienione — faza 6

- `persistence/project_io.py` zapisuje i czyta projekt przez
  `domain/project_schema.py`; `window.py` nie sięga już do `._data`.
- `persistence/settings.py` trzyma `QSettings` za jawną listą kluczy
  `theme`, `language`, `last_project`; bootstrap tworzy jedno `QSettings`.
- Zapis projektu używa klucza `"overlay"`. Odczyt nadal przyjmuje stary
  `"logo"`, ale nowy zapis go nie tworzy.
- Migracja ADR 0005: pozycje z `"overlay": true` bez `overlay_path` tracą
  flagę przy wczytaniu, z jednorazowym komunikatem; nowy kształt trafia do
  pliku dopiero po zapisie operatora.
- `tests/test_project_io.py` pokrywa zapis, round-trip, formaty legacy,
  migrację i błędy wejścia.

### Zmienione — poza refaktorem

- **Przejście media ↔ overlay przez kurtynę.** Włączenie i wyłączenie
  overlaya (F9, F10, checkbox pozycji) nie pokazuje już czarnej dziury, zanim
  VLC wystawi pierwszy obraz. Kurtyna to osobne okno top-level nad projekcją
  (natywne okno VLC zasłania zwykłe widżety): fade do czerni 120 ms, zmiana
  trybu w czerni, odsłonięcie 300 ms. Dla wideo kurtyna czeka na pierwszy
  obraz (`has_vout`, maks. 800 ms). To zmiana poza fazami refaktoru — faza 3
  była już ukończona.

### Zmienione — faza 3 (ADR 0005)

- **F9 nadpisuje overlay pozycji.** Przycisk zmienia nazwę na „Wymuś overlay",
  pokazuje overlay globalny i zasłania media oraz overlay bieżącej pozycji.
  Jest stanem do wyłączenia przez operatora, zerowanym przy starcie i przy
  wczytywaniu projektu. Przy braku assetu globalnego — wyszarzony.
- **Checkbox pozycji** znaczy wyłącznie „ta pozycja używa swojego overlaya";
  bez własnego assetu jest nieaktywny. Przypisanie assetu nie włącza już flagi
  automatycznie. Znika przypadek „użyj globalnego dla tej pozycji".
- **Migracja:** pozycje z `"overlay": true` i bez `overlay_path` tracą flagę
  przy wczytaniu, z jednorazowym komunikatem. Projekt zapisuje się w nowym
  kształcie dopiero po zapisie operatora.
- **Skutek:** pozycje, które wcześniej polegały na globalnym overlayu przez
  własną flagę, nie pokażą go już bez F9. To zmiana widoczna dla operatora —
  wydanie minor, nie patch.

## [0.7.2] — 2026-11-13

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
