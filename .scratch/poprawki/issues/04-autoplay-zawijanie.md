# 04: Autoplay — zawijanie i ruch wstecz

**What to build:** Autoplay po ostatniej pozycji wraca na początek playlisty,
a przejście wstecz działa również w trybie autoplay. Operator nie zostaje na
końcu scenariusza z martwym ekranem, a sterowanie „poprzedni" nie jest
ignorowane.

**Blocked by:** None (can start immediately)

**Status:** ready-for-human

- [x] Po ostatniej pozycji autoplay przechodzi na pierwszą
- [x] Przejście wstecz działa w trybie autoplay
- [x] Playlista z jedną pozycją nie zapętla się w nieskończoność bez przerwy
- [x] Przy wyłączonym autoplay dotychczasowe zachowanie bez zmian

## Comments

Realizacja: `domain/playlist.py` ma dwie czyste reguły wyboru wiersza.
`next_autoplay_row` zwraca następny wiersz i zawija z ostatniej pozycji na
pierwszą; `previous_autoplay_row` cofa o jeden bez zawijania z pierwszej na
ostatnią. Obie zwracają -1 dla pustej playlisty, wiersza spoza playlisty
i playlisty z jedną pozycją — jedyna pozycja zatrzymuje się na sobie.

`PlaybackSession` jest właścicielem „co dalej": `play_next`/`play_previous`
działają w trybie autoplay i liczą cel z odtwarzanej pozycji, a `play_row`
odtwarza go. Autoplay (koniec wideo `Ended` i koniec czasu obrazu) woła
`play_next`, więc nie zależy od zaznaczenia w widoku. Sesja pamięta czas
ekspozycji obrazu; `image_switch_delay.valueChanged` odświeża go na bieżąco,
więc zmiana w trakcie autoplay działa na kolejny obraz. `MainWindow` przy
włączonym autoplay deleguje przyciski next/previous do sesji, a
`_on_playing_row_changed` prowadzi zaznaczenie za odtwarzaną pozycją — gdy
filtr ją ukrywa, czyści zaznaczenie. Przy wyłączonym autoplay zostaje dawna
nawigacja po zaznaczeniu (`_play_selected_neighbor`), bez zawijania.

`GLOSSARY.md` rozdziela automatyczne przejście autoplay od ręcznego
next/previous i opisuje zawijanie tylko przy włączonym autoplay.

Weryfikacja: `pytest` — 105 zielonych (12 nowych testów reguł wiersza),
`ruff check .` czysto, `compileall` czysto. Harness offscreen na prawdziwym
`MainWindow`: next z ostatniej → pierwsza wraz z zaznaczeniem, previous
z odtwarzanej pozycji, brak pętli przy jednej pozycji, zmiana czasu ekspozycji
dociera do kolejnego obrazu, sesja nie rusza się poza autoplay, filtr
ukrywający następny wiersz nie blokuje autoplay, a przy wyłączonym autoplay
next/previous działają po zaznaczeniu i nie zawijają. Do potwierdzenia na
sprzęcie: autoplay po `Ended` wideo wraca na pierwszą pozycję, obraz przechodzi
po czasie ekspozycji, a previous w trakcie autoplay cofa odtwarzanie.
