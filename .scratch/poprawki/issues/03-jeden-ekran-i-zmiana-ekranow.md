# 03: Obsługa jednego ekranu i zmiany ekranów

**What to build:** Gdy jest tylko jeden ekran, operator dostaje czytelne
ostrzeżenie zamiast cichej projekcji 800×600 na konsoli. Podłączenie lub
odłączenie drugiego ekranu w trakcie pracy przestawia okno projekcji bez
restartu aplikacji — także wtedy, gdy ekran zniknie podczas odtwarzania.

**Blocked by:** None (can start immediately)

**Status:** ready-for-human

- [x] Przy jednym ekranie widać ostrzeżenie wyjaśniające, gdzie trafi projekcja
- [x] Ostrzeżenie nie blokuje startu aplikacji ani odtwarzania
- [x] Podłączenie drugiego ekranu po starcie przenosi projekcję na niego
- [x] Odłączenie drugiego ekranu nie wywala aplikacji i wraca na ekran operatora

## Comments

Realizacja: `ProjectionWindow.move_to_second_screen` jest teraz wspólnym
„ułóż projekcję": przy drugim ekranie ustawia go przez `setScreen` i włącza
pełny ekran, a przy jednym ekranie wychodzi z pełnego ekranu i stawia okno
800×600 na środku `availableGeometry()` ekranu podstawowego. Ukryte okno
zostaje ukryte — zmienia się tylko ekran, na którym się pokaże. Przy okazji
zniknęło stare przesunięcie liczone od `topLeft() + center()`, które przy
drugim monitorze po prawej odkładało okno poza ekran.

`MainWindow` podłącza `QApplication.screenAdded` i `screenRemoved` do
`_on_screens_changed`, który przestawia projekcję i odświeża ostrzeżenie, więc
podłączenie i odłączenie działają bez restartu, także w trakcie odtwarzania.
`ui/layout.py` dodaje na górze konsoli baner `ScreenWarningLabel` widoczny
tylko przy jednym ekranie; to zwykła etykieta, nie modal, więc nie blokuje
startu ani transportu. Tekst jest w `ui/i18n.py` (PL/EN), a motywy dostają
styl `QLabel#ScreenWarningLabel` na istniejących tokenach `bg_dark` i `fade`.

Weryfikacja: `pytest` — 89 zielonych, `ruff check .` czysto, `compileall`
czysto. Harness offscreen na prawdziwym `MainWindow`: baner widoczny przy
jednym ekranie, projekcja 800×600 wyśrodkowana, po `screenRemoved`/
`screenAdded` okno żyje i wraca do trybu okienkowego. Ścieżki z drugim
ekranem wymagają sprzętu — do potwierdzenia: podłączenie monitora przenosi
projekcję na pełny ekran, odłączenie w trakcie odtwarzania wraca na konsolę
bez przerwania playbacku.
