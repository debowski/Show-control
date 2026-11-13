# ADR 0001 — Pakiet `showcontrol/` z `main.py` jako bootstrapem

**Status:** przyjęta
**Data:** 2026-11-13
**Kontekst:** `docs/refactor-plan.md`, faza 1

## Kontekst

Cała aplikacja to `main.py` — 2147 linii, 65 metod w `App`. Chcemy podziału
na moduły, ale trzy rzeczy zależą od istnienia pliku `main.py` w katalogu
głównym:

1. CI buduje `pyinstaller main.py ...` (`.github/workflows/relase.yml:33`),
   mimo że w repo są dwa pliki `.spec`, których CI nie używa.
2. README instruuje `python main.py` (linia 233).
3. Użytkownicy mają skróty do `dist/main/main.exe` — nazwa pochodzi od
   `main.spec: name='main'`.

Istnieje też `ShowControl.spec` (nazwa `ShowControl`, `icon='NONE'`,
binaria w EXE), którego README każe używać, a którego CI ignoruje.

## Decyzja

`main.py` **zostaje** jako ośmiolinijkowy bootstrap:

```python
from showcontrol.app import main

if __name__ == "__main__":
    main()
```

Kod przenosi się do pakietu `showcontrol/` w katalogu głównym repo
(bez `src/`). Wersja żyje wyłącznie w `showcontrol/__init__.py`.

## Konsekwencje

**Pozytywne**

- CI, README i skróty użytkowników działają bez zmian.
- PyInstaller śledzi importy do pakietu — build `pyinstaller main.py`
  i `pyinstaller main.spec` dają ten sam wynik; nie trzeba `--hidden-import`.
- `main.py` w roocie czyta się jako „tu się zaczyna", niezależnie od tego,
  ile jest modułów.

**Negatywne**

- Repo ma plik `main.py` i katalog `showcontrol/` obok siebie — dwie nazwy
  na jedno. Zaakceptowane: koszt jednego pliku vs złamanie trzech rzeczy.
- Import pakietu wymaga, żeby katalog repo był w `sys.path`; PyInstaller i
  `python main.py` to zapewniają, ale `pytest` potrzebuje `pythonpath = ["."]`
  w konfiguracji.

## Odrzucone alternatywy

**`src/showcontrol/` + `main.py` jako shim** — dodaje konfigurację
(`pythonpath`, `package-dir`) i psuje `python main.py` dla kogoś, kto klonuje
repo bez instalacji. Przy jednym projekcie zero zysku.

**Usunięcie `main.py`** — łamie CI, README i skróty naraz.
