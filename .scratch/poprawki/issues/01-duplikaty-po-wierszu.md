# 01: Duplikaty dozwolone — operacje po wierszu, nie po ścieżce

**What to build:** Ten sam plik można dodać do playlisty wiele razy i każda
kopia jest niezależna: ma własny overlay, własne miejsce w scenariuszu i własny
wiersz. Przeciągnięcie kopii przenosi tę kopię, którą operator złapał, a nie
pierwszą o tej samej ścieżce. Zapis i odczyt projektu zachowuje liczbę kopii,
ich kolejność i przypisane overlaye.

**Blocked by:** None (can start immediately)

**Status:** ready-for-human

- [x] Dodanie tego samego pliku 3× daje 3 niezależne wiersze
- [x] Overlay ustawiony na drugiej kopii nie zmienia pierwszej
- [x] Przeciągnięcie drugiej kopii przenosi drugą, nie pierwszą
- [x] Usunięcie jednej kopii nie rusza pozostałych
- [x] Round-trip projektu zachowuje duplikaty, kolejność i overlaye per wiersz

## Comments

Realizacja: `PlaylistStore` już trzymał niezależne wpisy, więc duplikaty nie
były blokowane; problem siedział w dwóch miejscach kluczowanych ścieżką.
`PlaylistFilterProxyModel` implementuje teraz `moveRows`, mapując wiersze proxy
na wiersze modelu źródłowego. Dzięki temu `QListView` przy przeciąganiu
wewnętrznym przenosi dokładnie zaznaczony wiersz — nie pierwszy o tej samej
ścieżce. Wcześniej Qt nie umiało przenieść wiersza przez proxy, cofało się do
`dropMimeData` po ścieżce, a potem `clearOrRemove()` usuwało przeciągnięty
wiersz jako „przeniesiony" — stąd znikająca pozycja. `window.py` wczytuje
projekt w kolejności zapisu i nadaje overlaye po indeksie pozycji zamiast po
ścieżce, więc duplikaty zachowują własne overlaye po round-tripie. Nowa czysta
funkcja `partition_project_items` (`persistence/project_io.py`) rozdziela
pozycje istniejące i brakujące z zachowaniem kolejności. Zniknęło
`row_for_path` z modelu i magazynu — pierwsze trafienie po ścieżce było właśnie
źródłem błędu.

Weryfikacja: `pytest` — 89 zielonych, `ruff check .` czysto, import
`showcontrol.window` bez błędów. Harness headless (offscreen Qt) na prawdziwym
`PlaylistModel` i `PlaylistFilterProxyModel`: `moveRow` z wiersza drugiej kopii
przenosi ją wraz z overlayem (w dół i w górę), a upuszczenie pliku z
Eksploratora dokłada kolejną, niezależną kopię. Do potwierdzenia na sprzęcie:
przeciągnięcie drugiej kopii myszą — pozycja ma się przenieść, nie zniknąć.

