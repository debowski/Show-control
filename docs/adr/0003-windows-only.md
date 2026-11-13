# ADR 0003 — Windows-only, bez seamu platformowego

**Status:** przyjęta
**Data:** 2026-11-13
**Kontekst:** `docs/refactor-plan.md`, faza 2

## Kontekst

Rozważane były dwie drogi: dodać w przyszłości Linux albo zostać na Windows.

Fakt techniczny, który przesądził sprawę: **osadzanie obrazu z LibVLC
w widgecie Qt nie działa pod Waylandem.** libvlc dostaje uchwyt powierzchni,
którego nie potrafi użyć, i otwiera własne okno zamiast renderować w widgecie.
Problem jest zgłaszany niezależnie od frameworka (pympress #320, wątki
StackOverflow dla PyQt5/PyQt6 na Ubuntu z GNOME/Wayland). Działa X11 i XWayland.

Aplikacja wymaga więc osadzenia wideo w oknie projekcji — bez tego nie ma
produktu. Realny Linux oznaczałby `QT_QPA_PLATFORM=xcb` wymuszony na starcie
i deklarację „Wayland niewspierany", a dodatkowo inną ścieżkę bootstrapu
LibVLC (systemowe `libvlc.so` vs `libvlc.dll`), inny format ikony,
inny artefakt dystrybucyjny i drugi job w CI.

Niezależnie od tego: kod ma dziś `sys.platform.startswith("win")` bez żadnej
ścieżki alternatywnej — czyli sugeruje przenośność, której nie ma.

## Decyzja

**Windows-only, na stałe.** Konsekwencje w kodzie:

- `winId()` używane bezpośrednio; **nie powstaje** `playback/surface.py`
  ani żadna abstrakcja powierzchni wideo.
- Gałęzie `sys.platform` usunięte w fazie 2.
- README deklaruje Windows 10/11 jawnie, bez „na razie".
- CI pozostaje jednym jobem `windows-latest`.

## Konsekwencje

**Pozytywne**

- ~40 linii mniej kodu i o jedno miejsce mniej do przemyślenia przy każdym
  bugu związanym z projekcją.
- Brak pokusy „dodajmy abstrakcję, może się przyda" — decyzja jest zapisana
  i ma uzasadnienie techniczne, nie estetyczne.

**Negatywne**

- Dodanie Linuksa później oznacza dotknięcie `playback/engine.py`
  i `playback/session.py`. Szacunek: nie seam, a przepisanie ~400 linii.
- Ktoś może zgłosić issue „nie działa na Macu" — odpowiedź jest w tym ADR.

## Odrzucone alternatywy

**Seam `VideoSurface` teraz, implementacja linuksowa później** — abstrakcja
z jedną implementacją to koszt bez zysku; interfejs wymyślony bez drugiego
użycia prawie zawsze jest zły i i tak się go przepisuje.

**X11-only Linux teraz** — podwaja zakres CI i dystrybucji, a produkt jest
używany na Windows. Nie ma popytu, jest koszt.

**Natywny Wayland (libmpv zamiast VLC)** — wymiana silnika odtwarzania.
Osobny projekt, nie faza refaktoru.
