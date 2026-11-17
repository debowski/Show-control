# 08: Czyszczenie globalnego overlaya, wskaźnik stanu i wczytanie projektu bez overlaya

**What to build:** Operator może jednym przyciskiem usunąć globalny overlay,
bez okna potwierdzenia. Przycisk „Wybierz overlay" ma obok siebie stale widoczny
wskaźnik stanu: nazwę ustawionego pliku albo „brak". Po wyczyszczeniu projekcja
natychmiast wraca do mediów i overlaya pozycji, „Wymuś overlay" gaśnie i jest
zablokowany, a projekt zapisuje się bez overlaya. Wczytanie projektu bez
overlaya również zabiera overlay z poprzedniego projektu, a wskaźnik pokazuje
„brak".

**Blocked by:** None (kolejność po 06 zmniejsza konflikt w tym samym fragmencie)

**Status:** ready-for-human

- [x] Przycisk „Wyczyść overlay" obok „Wybierz overlay", bez potwierdzenia
- [x] Wskaźnik stanu pokazuje nazwę pliku albo „brak" i aktualizuje się po wyborze, czyszczeniu i wczytaniu projektu
- [x] Po wyczyszczeniu projekcja pokazuje media/overlay pozycji, nie ostatni globalny asset
- [x] „Wymuś overlay" odznacza się i jest zablokowany, gdy overlay jest „brak"
- [x] Zapis projektu utrwala brak overlaya, odczyt nie wskrzesza starego
- [x] Wczytanie projektu z `overlay: null` czyści overlay z poprzedniego projektu

## Comments

Realizacja: `ui/layout.py` dodaje `clear_overlay_btn` i stale widoczny
`overlay_status_label` obok „Wybierz overlay"; `window.py` spina wybór,
czyszczenie i wczytanie projektu przez `_set_global_overlay`, a
`_sync_overlay_controls` aktualizuje etykietę, blokuje „Wymuś overlay" i zeruje
jego zaznaczenie bez sygnałów. `playback/overlay.py` odróżnia wyczyszczony
globalny asset od assetu pozycji, dzięki czemu projekcja wraca od razu do
mediów/overlaya pozycji bez fade'u od ostatniego globalnego pliku.
`domain/overlay_rules.py` nie włącza już trybu overlay dla F10 bez assetu
globalnego. Zapis i odczyt projektu przenoszą `overlay: null` bez zmian.

Weryfikacja: `pytest` — 84 zielone, `compileall` czysto; harness headless na
`OverlayController` potwierdza powrót do mediów po wyczyszczeniu, zachowanie
overlaya pozycji i przełączenie na nowy asset. Do potwierdzenia na sprzęcie:
natychmiastowy obraz na projekcji po „Wyczyść overlay" oraz zgaszony i
zablokowany „Wymuś overlay" bez globalnego assetu.
