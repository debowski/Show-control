# AGENTS.md

Kontekst dla agentów pracujących w tym repo. Czytaj razem z
`docs/refactor-plan.md` i `GLOSSARY.md`.

## Co to jest

Aplikacja desktopowa Windows dla operatorów wydarzeń na żywo: dwuekranowe
odtwarzanie multimediów (konsola operatora + okno projekcji). Python 3.10+,
PyQt6, LibVLC przez `python-vlc`. GPL-3.0.

## Twarde ograniczenia

- **Windows-only.** Nie dodawaj gałęzi `sys.platform`, nie dodawaj abstrakcji
  pod Linux/macOS. Uzasadnienie: `docs/adr/0003-windows-only.md`.
- **Jedno źródło wersji:** `showcontrol/__init__.py:__version__`. Nie wpisuj
  numeru wersji w żadnym innym pliku.
- **Formatowanie osobno.** `ruff` działa w trybie błędów (`E4,E7,E9,F`).
  `ruff format` obowiązuje od fazy 7 i idzie w osobnym commicie — nigdy
  zmieszany ze zmianą logiki.
- **Nie zmieniaj zachowania** poza fazą 0. Nowe funkcje nie wchodzą w refaktor.
- **`domain/*` nie importuje Qt ani vlc.** Warunek testów.
- **Nie dodawaj `shortcuts.json` z powrotem** — jedyne źródło skrótów to
  `ui/shortcuts.py`.

## Gdzie co jest

Stan bieżący: fazy 0–7 ukończone, brama sprzętowa zdana; zostaje brama
release (tag buduje exe). `main.py` to bootstrap; kod w `showcontrol/`
(`window.py` spina moduły, `ui/layout.py` buduje panele operatora, `domain/`,
`ui/`, `playback/*`, `persistence/*`). Testy w `tests/` — domain, ustawienia,
motyw i projekt; bez Qt i VLC.
Stan docelowy i mapa modułów: `docs/refactor-plan.md`, sekcja 4.

Pytania „co to znaczy X" rozstrzyga `GLOSSARY.md`, nie kod. Jeśli kod używa
nazwy sprzecznej z glosariuszem, kod jest błędny.

## Komendy

```bash
python main.py                    # uruchomienie
pyinstaller main.spec             # build (wymaga PyInstaller 6.20.0)
py -3.14 -m pytest                # testy (wymagają PyQt6 i python-vlc)
ruff check .                      # lint błędów
```

## Bramy odbioru

Faza jest gotowa tylko wtedy, gdy wszystkie pięć:

1. `python main.py` startuje,
2. build przechodzi,
3. exe odtwarza wideo, audio i obraz, overlay i fade,
4. testy zielone,
5. `git diff` w README tylko w miejscach build/ścieżki.

Punkty 3 wymaga sprzętu z drugim ekranem — nie da się go zastąpić testem.

## Znane defekty

Lista w `docs/refactor-plan.md`, sekcja 6. To **osobne tickety**, nie część
refaktoru. Jeśli natrafisz na nie przy przenoszeniu kodu: przenieś zachowanie
1:1 i dopisz komentarz `# TODO(defekt N)`, nie naprawiaj.

## Styl pracy

- Jedno cięcie = jeden commit. Zmiany nazw osobno od zmian logiki.
- Komunikaty commitów: `typ(zakres): opis` (`fix(ui):`, `refactor(playback):`,
  `docs(adr):`). Nie „Tak correction".
- Po każdej fazie: aplikacja sprawna. Nie zostawiaj gałęzi w stanie
  pośrednim, w którym exe nie działa.

## Agent skills

### Issue tracker

Tickety i spece jako pliki w `.scratch/`. Patrz `docs/agents/issue-tracker.md`.

### Triage labels

Domyślne role triage jako wartości `Status:`. Patrz
`docs/agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` + `docs/adr/`. Patrz `docs/agents/domain.md`.

Skille instaluje się z `skills-lock.json`: `npx skills experimental_install`.
