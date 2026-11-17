# 01: Duplikaty dozwolone — operacje po wierszu, nie po ścieżce

**What to build:** Ten sam plik można dodać do playlisty wiele razy i każda
kopia jest niezależna: ma własny overlay, własne miejsce w scenariuszu i własny
wiersz. Przeciągnięcie kopii przenosi tę kopię, którą operator złapał, a nie
pierwszą o tej samej ścieżce. Zapis i odczyt projektu zachowuje liczbę kopii,
ich kolejność i przypisane overlaye.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Dodanie tego samego pliku 3× daje 3 niezależne wiersze
- [ ] Overlay ustawiony na drugiej kopii nie zmienia pierwszej
- [ ] Przeciągnięcie drugiej kopii przenosi drugą, nie pierwszą
- [ ] Usunięcie jednej kopii nie rusza pozostałych
- [ ] Round-trip projektu zachowuje duplikaty, kolejność i overlaye per wiersz
