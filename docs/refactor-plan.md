# Plan refaktoru Show Control

**Status:** zatwierdzony kierunek; fazy 0–2 ukończone (2026-11-16)
**Punkt wyjścia:** `v0.7.1` (`5cfcc81`)
**Właściciel:** solowy maintainer
**Zakres:** A (rozbicie monolitu) + C (model domenowy) → potem B (niezawodność)

---

## 1. Po co

Aplikacja działa i jest używana na żywo. Refaktor nie jest więc naprawianiem
czegoś zepsutego — jest inwestycją w to, żeby po pół roku przerwy dało się
wrócić do kodu i żeby dało się dopisać fazę B (niezawodność), nie przepisując
wszystkiego.

Kryterium podziału nie jest „ładnie", tylko: **dokąd idę, gdy coś się psuje
podczas wydarzenia**. Każdy moduł musi odpowiadać na jedno pytanie.

## 2. Stan wyjściowy (fakty, `v0.7.1`)

| Metryka | Wartość |
|---|---|
| `main.py` | 2147 linii, 91 538 B, jeden moduł |
| `App(QMainWindow)` | 1122 linie (52% pliku), 65 metod |
| `App.init_ui()` | 312 linii |
| `generate_stylesheet()` | 229 linii |
| `PlaylistModel` | 217 linii |
| `PlaylistItemDelegate` | 102 linie |
| Testy | 0 |
| Linter / formatter / typy | brak |
| TODO / FIXME | 0 |
| ADR / glosariusz / changelog | brak |
| `except Exception` | 11 z 12 klauzul `except` |
| `._data` poza modelem | 4 z 25 odwołań |
| Wersja zapisana w | 3 miejsca (`main.py:1`, `main.py:1021`, `README.md:282`) + tagi |

Stan rozproszony: `PlaylistModel._data`, 8 atrybutów `App`
(`is_playing`, `is_transitioning`, `user_is_seeking`, `_fade_state`,
`image_autoplay_start`, `image_autoplay_duration`, `_logo_path`,
`_current_playing_logo_path`), sygnały Qt i polling `QTimer` co 500 ms.

## 3. Zasady obowiązujące w całym refaktorze

1. **Zachowanie bez zmian**, poza dwoma świadomie wypisanymi wyjątkami:
   fazą 0 (fade 0–1 s) i decyzją F9 z ADR 0005 (faza 3). Jeśli coś innego
   wygląda na bug — ląduje w sekcji 6, nie w commicie refaktorowym.
2. **Windows-only.** Żadnych gałęzi `sys.platform`, żadnych abstrakcji pod
   przyszłe platformy. Patrz `docs/adr/0003-windows-only.md`.
3. **Jedno źródło wersji** — `showcontrol/__init__.py:__version__`.
   Nagłówek `main.py` i README przestają ją duplikować.
4. **Jedno źródło builda** — `main.spec` (faza 7). Do tego czasu build
   pozostaje nietknięty.
5. **Bez formatowania kodu.** `ruff` działa w trybie błędów (`E4,E7,E9,F`),
   nie formatuje. `ruff format` wchodzi najwcześniej w fazie 7, jako osobny
   commit, żeby nie zmieszać go z cięciem modułów.
6. **Każda faza kończy się bramą** (sekcja 9). Bramy 3–6 wymagają
   uruchomienia na sprzęcie z drugim ekranem.
7. **Bez nowych funkcji.** Ustawienia, których dziś nie ma w `QSettings`,
   nie pojawiają się w tym refaktorze.
8. **`domain/*` nie importuje Qt ani vlc.** To warunek testów.

## 4. Struktura docelowa

```
main.py                  8    bootstrap (CI i README działają bez zmian)
showcontrol/
  __init__.py            —    __version__ = jedyne źródło prawdy
  bootstrap.py          60    QApplication, motyw, log do pliku, crash handler
  window.py            200    MainWindow: spina moduły, zero logiki VLC
  ui/
    layout.py          250    init_ui (312) rozbite na 3 panele
    playlist_view.py   230    View + Delegate + Proxy (1:1)
    projection.py      180    ProjectionWindow + OverlayViewer
    shortcuts.py        90    tabela skrótów (zastępuje shortcuts.json)
    theme.py           240    THEMES + QSS (1:1)
    i18n.py            120    TRANSLATIONS + Translator (koniec sniffowania tekstu)
  domain/
    media.py            50    rozszerzenia, klasyfikacja plików
    playlist.py        200    PlaylistStore (model + operacje na wierszach)
    overlay_rules.py    60    precedencja overlay, czysta funkcja   ← testy
    project_schema.py  100    schemat + wersja + migracje, zero Qt   ← testy
  playback/
    engine.py          120    Instance + 2 MediaPlayer + hwnd + volume/brightness
    session.py         280    transport, autoplay, polling, transition guard
    fade.py             80    FadeController (stan przejścia, nie UI)
    overlay.py          90    ładowanie assetu + tryb projekcji
  persistence/
    project_io.py       80    save/load
    settings.py         50    QSettings z jawną listą kluczy
tests/
  test_overlay_rules.py      precedencja overlay
  test_project_schema.py     back-compat i migracje JSON
  test_playlist.py           operacje na wierszach
```

Suma rośnie (~2400 linii z 2147) — granice kosztują. `App` 1122 → `window.py` 200.

**Właścicielstwo stanu po refaktorze:** `session.py` wie, co teraz gra;
`fade.py` wie, w jakim stanie jest przejście; `ui/` tylko czyta i rysuje.
Dziś to jeden worek na `App`.

## 5. Fazy

### Faza 0 — trzy commity przed cięciem → tag `v0.7.2`

Kolejność ma znaczenie: refaktor startuje z gruntu, o którym wiadomo, że jest
poprawny — inaczej nie odróżnisz „zepsułem przy przenoszeniu" od „było zepsute".

| # | Commit | Zmiana |
|---|---|---|
| 0.1 | `fix(bootstrap): komunikat zamiast NameError bez python-vlc` | `TRANSLATIONS` używane w `main.py:28`, a definiowane w `main.py:40`. Przenieść definicję stałych języka przed blok `try/except import vlc` albo przenieść cały komunikat do `bootstrap.py`. |
| 0.2 | `fix(ui): etykieta fade pokazuje realną wartość` | `setValue(8)` (`main.py:1285`) wykonuje się przed `valueChanged.connect` (`main.py:1287`), więc etykieta zostaje na wpisanym `"2.0s"`, a fade realnie trwa 0.8 s. Podłączyć sygnał przed ustawieniem wartości. |
| 0.3 | `feat(fade): zakres 0–1 s` | `setRange(0, 10)` zamiast `(2, 20)`, `_fade_duration()` = `value/10`, domyślnie 8 (= 0.8 s, czyli dzisiejsze realne zachowanie). Logika kroków **bez zmian**: `steps = max(5, int(fade_secs*10))`, interwał ~100 ms, `0` daje 5 kroków po 1 ms. README: dwa miejsca z „0.2–2.0" → „0–1.0". Patrz `docs/adr/0004-fade-0-1s.md`. |

**Brama:** aplikacja startuje, fade pokazuje prawdę, projekcja gra.

### Faza 1 — szkielet pakietu, `domain/`, testy

Kolejność wewnątrz fazy jest istotna:

1. `showcontrol/__init__.py` z `__version__`; `main.py` → bootstrap wywołujący
   `showcontrol.app.main()`. `bootstrap.py` przejmuje przy okazji dwie
   duplikacje: `QSettings` konstruowany dziś dwa razy (`main.py:1020`, `2142`)
   oraz motyw aplikowany dwa razy (`2133–2134`, `2144`), a blok rozwiązywania
   ikony (`603–612` vs `1025–1034`) zostaje w jednym miejscu.
2. Przenieść **liściaste** moduły bez zmiany logiki: `ui/theme.py`
   (`THEMES` + `generate_stylesheet`, 1:1), `ui/i18n.py`
   (`TRANSLATIONS` + `get_t`, jeszcze bez usuwania sniffowania).
3. Wydzielić `domain/`: `media.py` (funkcje `is_audio_file`, `is_image_file`,
   `has_extension`, `find_media_paths`), `playlist.py` (`PlaylistModel` →
   `PlaylistStore`), `overlay_rules.py` (logika z `_set_projection_mode_for_path`,
   1736–1759), `project_schema.py` (z `_load_project_file`, 2075–2123).
   **`App` nadal deleguje do nich — zachowanie identyczne.**
4. Dopiero teraz `tests/` — 3 pliki, ~40 asercji, bez Qt i bez VLC.

**Brama:** `python main.py` startuje, `pyinstaller main.spec` buduje exe,
3 testy zielone.

### Faza 2 — `playback/engine.py`

`vlc.Instance` + dwa `MediaPlayer` + `set_hwnd` + volume + brightness + mute
overlaya. `App` dostaje `self.engine`, przestaje trzymać `winId()`.
Usunięcie gałęzi `sys.platform.startswith("win")` — zostaje ścieżka Windows.

**Brama:** wideo, audio i obraz grają; zmiana jasności i głośności działa.

### Faza 3 — `playback/fade.py` + `playback/overlay.py`

`_fade_state` i `is_transitioning` → `FadeController`. Ładowanie assetu
overlay i tryb projekcji → `overlay.py` (używa `domain/overlay_rules.py`).
Znikają dwa niemal identyczne bloki: `_load_overlay_media` (1761–1792)
i `update_logo_media` (1977–2010) — **jedno jądro ładowania**, bo ich guardy
już się rozjechały (`_load_overlay_media(None)` wychodzi wcześniej niż
`update_logo_media` z tymi samymi danymi). Jedno „aktualnie załadowany asset"
zamiast `_logo_path` + `_current_playing_logo_path`. `LogoViewer` →
`OverlayViewer`.

**Zmiana zachowania w tej fazie (ADR 0005).** F9 ma nadpisywać, nie tylko
włączać: gdy jest włączony, projekcja pokazuje overlay globalny i zasłania
media oraz overlay pozycji. F9 jest stanem do wyłączenia przez operatora,
nie jest zapisywany w projekcie i jest zerowany przy starcie oraz przy
wczytywaniu projektu. Checkbox pozycji znaczy wyłącznie „ta pozycja używa
swojego overlaya" — bez własnego assetu jest nieaktywny. Precedencja:
`GLOSSARY.md` § Precedencja.

To **nie jest** przenoszenie kodu: osobny commit, osobna brama (override działa
na sprzęcie), a w changelogu pozycja oznaczona jako zmiana zachowania.

**Brama:** F9, F10, overlay per-pozycja, fade, przywrócenie jasności po fade.

### Faza 4 — `playback/session.py`

Transport (`play_media`, `toggle_play_pause`, `stop_media`, `_finish_stop_media`,
`play_next_file`, `play_previous_file`), autoplay, polling 500 ms,
`_start_media_transition` / `_finish_media_transition`, `user_is_seeking`.
`App` traci `is_playing`, `_current_media_path()` i logikę „co jest teraz
odtwarzane". Własność `playing_row` przechodzi z modelu do sesji — `GLOSSARY.md`
definiuje „odtwarzaną pozycję" jako stan sesji, a model dostaje tylko wskaźnik
do narysowania.

**Wymóg projektowy fazy B:** sesja ma **jedno** miejsce, w którym da się
podpiąć recovery (np. `SessionState` + `on_failure`). Bez tego faza 8 zamienia
się w przepisywanie tej fazy.

**Brama:** next/prev/autoplay/stop, obraz po zadanym czasie, przejścia bez
mignięć.

### Faza 5 — `ui/*` i `window.py`

`init_ui` (312 linii) → 3 panele w `ui/layout.py`. Podział na
`ui/playlist_view.py`, `ui/projection.py`, `ui/shortcuts.py` (tabela skrótów
jako jedyne źródło — `shortcuts.json` przestaje być potrzebny).
`apply_translations` przestaje rozpoznawać widżety po treści (`main.py:1459–1491`)
— dostają stabilne identyfikatory. `App` → `window.py` (~200 linii).

Trzy rzeczy, które ta faza musi domknąć, bo inaczej zostają na zawsze:

- **Skróty**: jedna tabela niosąca klawisz, akcję i etykietę; znika
  `KEY_TOOLTIP_LABELS`, a `update_shortcut_descriptions` przestaje być
  drugim źródłem tych samych stringów co `apply_translations`.
- **Motyw**: tokeny czytane także przez delegate i etykiety inline — dziś
  `#444444`, `#883333`, `#094771` i trzy `#aaaaaa` omijają `THEMES`,
  a `list_play` nie ma żadnego konsumenta.
- **Teksty poza systemem**: ~44 miejsca z polskim tekstem na sztywno
  (`EMPTY_TIME_LABEL`, filtr dialogu, komunikaty zapisu/odczytu, tooltipy
  modelu, „Spacja"). Trzeci język ma być dopisaniem danych, nie kodu.

**Brama:** przełączanie PL/EN w obie strony bez restartu, 4 motywy,
wszystkie skróty z README działają, feedback przycisków.

### Faza 6 — `persistence/*`

`project_io.py` (save/load na `domain/project_schema.py`), `settings.py`
(`QSettings` z jawną listą kluczy: `theme`, `language`, `last_project`).
Znikają odwołania do `._data` spoza modelu (`2057`, `2106`, `2110`, `2113`).
Klucz `"logo"` w JSON projektu (`main.py:2061`) → `"overlay"`; ADR 0002 go nie
wymienia, więc to osobna pozycja tej fazy, z migracją starego klucza.

**Migracja z ADR 0005:** pozycje z `"overlay": true` i `"overlay_path": null`
znaczyły dotąd „pokaż overlay globalny". Przy wczytaniu flaga jest czyszczona,
a operator dostaje jednorazowy komunikat. Projekt zapisuje się w nowym kształcie
dopiero, gdy operator sam zapisze.

**Brama:** zapis projektem, odczyt, stare formaty (goła lista, stringi),
brakujący plik nie wywala aplikacji.

### Faza 7 — build i porządki

Jeden spec: `main.spec`; `ShowControl.spec` usunięty; README wskazuje
`main.spec`; CI woła `pyinstaller main.spec` zamiast komendy inline
(`relase.yml:33`); `relase.yml` → `release.yml`; CI przestaje kopiować
`shortcuts.json`. Usunięcie `shortcuts.json`, `app036.png`,
`__pycache__/main.cpython-314.pyc`; `.gitignore` przestaje ignorować `*.spec`
(dwa pliki są w repo). `ruff format` jako osobny commit. `requirements.txt`
z przypiętymi wersjami albo przejście na `pyproject.toml`.

**Brama:** release z taga buduje ten sam exe, który powstał lokalnie.
Patrz `docs/adr/0001-pakiet-z-bootstrapem.md` — punkt o kompatybilności.

### Faza 8 — B: niezawodność (szkic, nie implementacja)

Jedna strona, bez decyzji:
1. Log do pliku (`logging` → `%LOCALAPPDATA%`), bo build `-w` nie ma stderr.
2. Powierzchnia błędów w UI zamiast `print()` przy brakujących plikach.
3. Zamknięcie z niezapisanymi zmianami — potwierdzenie.
4. Autosave / recovery ostatniego projektu.
5. Zachowanie przy zniknięciu drugiego ekranu i przy awarii VLC.

## 6. Znane defekty — świadomie poza zakresem

Nie naprawiamy w tym refaktorze. Każdy osobny ticket.

| # | Defekt | Gdzie |
|---|---|---|
| 1 | Duplikaty ścieżek na playliście; przesuwanie trafia w zły wiersz | `main.py:804–821`, `743–747` |
| 2 | Usunięcie odtwarzanej pozycji nie zatrzymuje playbacku | `main.py:759–768` |
| 3 | Jeden ekran → projekcja 800×600 na ekranie operatora, bez ostrzeżenia | `main.py:627–635` |
| 4 | Brak obsługi zmiany ekranów po starcie | tamże |
| 5 | `shortcuts.json` (`search: "f"`, `fade_out: F8`) sprzeczny z kodem (F3, F1) | plik + `main.py:133–162` |
| 6 | `file_paths()` nigdy nie wywoływane | `main.py:829–830` |
| 7 | `list_play` w `THEMES` nigdy nie użyty; podświetlenie zawsze `#094771` | `main.py:676` |
| 8 | Autoplay nie zawija na końcu i nie chodzi wstecz | `main.py:1811–1826` |
| 9 | Brak „wyczyść playlistę", usuwanie tylko pojedyncze | `main.py:1676` |
| 10 | Czas w etykiecie zaszyty po polsku („Pozostało") niezależnie od języka | `main.py:36`, `1639`, `1647` |
| 11 | Błędy zapisu/odczytu pokazują surowy wyjątek, po polsku | `main.py:2068`, `2123` |
| 12 | Brak walidacji uszkodzonego JSON poza generycznym `try` | `main.py:2075+` |
| 13 | Dialog „Dodaj pliki" nie przyjmuje 8 z 13 obsługiwanych rozszerzeń: brak `.wav`, `.flac`, `.aac`, `.ogg`, `.m4a`, `.jpeg`, `.bmp`, `.gif` | `main.py:35` |
| 14 | Projekt bez overlaya nie czyści poprzedniego — stary overlay zostaje na projekcji | `main.py:2116–2118` |

Wersjonowanie: tagi `v0.3.9`–`v0.4.2` wskazują kod z nagłówkiem `0.3.7`;
`v0.3.5`/`v0.3.6` to ten sam commit; `v0.4.2 → v0.7.1` to 4 linie kodu.
`v0.7.1` = nowa linia bazowa, ciągłość 0.5/0.6 nie istnieje.

## 7. Decyzje odrzucone

Zapisane, żeby nie wracały:

| Odrzucone | Dlaczego |
|---|---|
| Linux / macOS | `docs/adr/0003-windows-only.md`; osadzanie VLC pod Waylandem nie działa |
| `playback/surface.py` (seam platformowy) | abstrakcja bez drugiej implementacji |
| `src/` layout | jeden projekt, zero zysku, łamie `python main.py` i CI |
| `pytest-qt` na całe UI | kruche przy VLC, wysoki koszt utrzymania |
| Dwa pliki `.spec` | cztery źródła prawdy o buildzie |
| `shortcuts.json` jako źródło skrótów | duplikat tabeli w kodzie, dziś nieczytany |
| Dokładanie kluczy do `QSettings` | to funkcja, nie refaktor |
| `RUFF format` od razu | 2147 linii diffu zmieszane z cięciem modułów |
| Szablony issue/PR | jeden maintainer, zero ruchu w issues |
| F9 jako „dodaj overlay", nie nadpisanie | ADR 0005: operator oczekuje zasłonięcia |
| F9 jako przytrzymanie klawisza | niepraktyczne przy kilkuminutowym utworze |
| Materializacja globalnego assetu do pozycji | podmienia dane operatora bez wiedzy; ADR 0005 |
| Zapisywanie F9 w projekcie | start z brandingiem zamiast pierwszej pozycji |

## 8. Ryzyka

| Ryzyko | Reakcja |
|---|---|
| Osadzanie VLC psuje się przy przenoszeniu `winId()` | brama fazy 2 wymaga uruchomienia na drugim ekranie |
| `init_ui` rozbijane „na wyczucie" gubi kolejność widgetów | cięcie po panelach, nie po typach; 1:1 przed upiększeniem |
| Testy na `domain/*` przechodzą, a aplikacja nie | brama fazy 1 = exe + ręczne uruchomienie |
| Refaktor utyka w połowie | fazy 2–6 są niezależne; po każdej aplikacja jest sprawna |
| Operator zapomni, że F9 jest włączony | widoczny stan kontrolki + oznaczenie przesłoniętych wierszy; F9 zerowany przy starcie |
| `except Exception` maskuje regresje przy przenoszeniu | po fazie 4 zamienić 11 klauzul na konkretne wyjątki, osobny commit |

## 9. Bramy — definicja „gotowe"

Zatwierdzone kryterium odbioru fazy:

1. `python main.py` startuje.
2. `pyinstaller main.spec` buduje exe.
3. Exe odtwarza wideo, audio i obraz, overlay i fade.
4. Testy zielone.
5. `git diff` w README tylko w miejscach build/ścieżki.

Faza gotowa, gdy wszystkie pięć. Bez punktu 3 to nie refaktor, tylko
przestawianie plików.

## 10. Rejestr decyzji

| ADR | Decyzja |
|---|---|
| [0001](adr/0001-pakiet-z-bootstrapem.md) | pakiet `showcontrol/` + `main.py` jako bootstrap |
| [0002](adr/0002-overlay-zamiast-logo.md) | „overlay" zamiast „logo"; jedna semantyka |
| [0003](adr/0003-windows-only.md) | Windows-only, bez seamu platformowego |
| [0004](adr/0004-fade-0-1s.md) | fade 0–1 s, domyślnie 0.8 s |
| [0005](adr/0005-f9-nadpisuje-overlay.md) | F9 nadpisuje overlay; checkbox = własny overlay |

## 11. Przegląd architektury — 2026-11-13

Niezależne przejście po `v0.7.1` (raport HTML w katalogu tymczasowym systemu).
Wynik: **plan nie potrzebuje nowych faz** — dziewięć kandydatów mieści się
w istniejących, ale cztery rzeczy były niedoprecyzowane i zostały dopisane
do faz powyżej.

| # | Kandydat | Siła | Faza | Co dopisano |
|---|---|---|---|---|
| C1 | Stan odtwarzania jako worek 8 atrybutów + timer 500 ms | Strong | 4 | `playing_row` przechodzi do sesji |
| C2 | Tryb projekcji zapisywany trzema kanałami | Strong | 3 / 1 | decyzja: F9 nadpisuje (ADR 0005) |
| C3 | `PlaylistModel`: 19 metod, 4 układy współrzędnych | Worth | 1 / 4 | przekazanie własności wskaźnika |
| C4 | Fade: słownik 7 kluczy + 3 parametry, które muszą się zgadzać | Worth | 3 | zachowanie formuły z ADR 0004 |
| C5 | Ładowanie overlaya: jedna implementacja dwa razy, rozjechane guardy | Strong | 3 | jedno jądro ładowania, jeden „loaded asset" |
| C6 | Tłumaczenia rozpoznają widżety po tekście | Worth | 5 | trzeci język, 44 teksty poza systemem |
| C7 | Skróty w pięciu strukturach + nieczytany JSON | Worth | 5 / 7 | jedna tabela, usunięcie kopii z CI |
| C8 | Tokeny motywu omijane przez delegate i etykiety | Worth | 5 | osiągalność token → konsument |
| C9 | Interfejs `App` szeroki jak implementacja | Speculative | 1–5 | duplikacje startu i ikony |

**Czego przegląd nie zmienił:** kolejności faz, kryteriów odbioru, decyzji
o Windows-only, zakresu fade'a ani podziału modułów. Wszystkie kandydaty
lokują się w istniejących bramach.

**Najważniejsza zmiana merytoryczna:** `GLOSSARY.md` twierdził, że F9 jest
najsilniejszym nadpisaniem trybu projekcji, a kod mówił inaczej — F9 tylko
**włączał** overlay globalny. Przegląd ujawnił sprzeczność; decyzja operatora
(2026-11-13) brzmi: **kod ma się zmienić, nie dokument**. Patrz
`docs/adr/0005-f9-nadpisuje-overlay.md`. To jedyne miejsce, w którym ten
refaktor świadomie zmienia zachowanie poza fazą 0.

**Dwa nowe defekty** dopisane do sekcji 6: filtr dialogu „Dodaj pliki"
(13) i nieczyszczony overlay przy wczytaniu projektu bez overlaya (14).
