# 09: Usunięcie martwego `file_paths`

**What to build:** Znika nieużywana metoda zwracająca ścieżki playlisty oraz jej
test. Zachowanie aplikacji się nie zmienia — to sprzątanie po refaktorze, bez
wpływu na operatora.

**Blocked by:** None (can start immediately)

**Status:** ready-for-human

- [x] Metoda `file_paths` znika z modelu playlisty i magazynu
- [x] Test pokrywający tę metodę znika razem z nią
- [x] Testy i lint są zielone, aplikacja startuje bez zmian

## Comments

Realizacja: usunięta `PlaylistStore.file_paths` w `domain/playlist.py` oraz
przekazująca ją `PlaylistModel.file_paths` w `ui/playlist_view.py`. Nie miały
innych wywołań w kodzie. Test dedykowany metodzie zniknął, a dwa testy, które
korzystały z niej pomocniczo, czytają ścieżki z `store.rows()`.

Weryfikacja: `pytest` — 104 zielone (o jeden mniej niż przed zmianą, bo zniknął
test usuniętej metody), `python -m ruff check .` czysto. Aplikacja startuje bez
zmian — usunięcie dotyczyło wyłącznie nieużywanego API.
