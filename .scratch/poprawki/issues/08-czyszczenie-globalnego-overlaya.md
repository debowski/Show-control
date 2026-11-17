# 08: Czyszczenie globalnego overlaya, wskaźnik stanu i wczytanie projektu bez overlaya

**What to build:** Operator może jednym przyciskiem usunąć globalny overlay,
bez okna potwierdzenia. Przycisk „Wybierz overlay" ma obok siebie stale widoczny
wskaźnik stanu: nazwę ustawionego pliku albo „brak". Po wyczyszczeniu projekcja
natychmiast wraca do mediów i overlaya pozycji, „Wymuś overlay" gaśnie i jest
zablokowany, a projekt zapisuje się bez overlaya. Wczytanie projektu bez
overlaya również zabiera overlay z poprzedniego projektu, a wskaźnik pokazuje
„brak".

**Blocked by:** None (kolejność po 06 zmniejsza konflikt w tym samym fragmencie)

**Status:** ready-for-agent

- [ ] Przycisk „Wyczyść overlay" obok „Wybierz overlay", bez potwierdzenia
- [ ] Wskaźnik stanu pokazuje nazwę pliku albo „brak" i aktualizuje się po wyborze, czyszczeniu i wczytaniu projektu
- [ ] Po wyczyszczeniu projekcja pokazuje media/overlay pozycji, nie ostatni globalny asset
- [ ] „Wymuś overlay" odznacza się i jest zablokowany, gdy overlay jest „brak"
- [ ] Zapis projektu utrwala brak overlaya, odczyt nie wskrzesza starego
- [ ] Wczytanie projektu z `overlay: null` czyści overlay z poprzedniego projektu
