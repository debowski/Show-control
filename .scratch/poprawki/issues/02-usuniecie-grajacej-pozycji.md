# 02: Usunięcie odtwarzanej pozycji zatrzymuje playback

**What to build:** Skasowanie wiersza, który właśnie gra, kończy odtwarzanie:
dźwięk i obraz znikają, wskaźnik odtwarzania się czyści, a operator widzi stan
spoczynku. Dziś playback leci dalej, mimo że nie ma już wiersza, do którego
należy.

**Blocked by:** None (can start immediately)

**Status:** ready-for-human

- [x] Usunięcie odtwarzanej pozycji zatrzymuje media (audio i wideo)
- [x] Wskaźnik odtwarzania i czas wracają do stanu spoczynku
- [x] Usunięcie pozycji, która nie gra, nie przerywa bieżącego odtwarzania
- [x] Zachowanie działa także przy usuwanym wierszu ukrytym przez filtr

## Comments

Realizacja: `PlaybackSession.on_rows_removed` wykrywa usunięcie odtwarzanej
pozycji (przez `adjust_row_for_remove`) i emituje `playing_row_removed`. Okno
łączy ten sygnał ze `stop_media`, więc zatrzymanie idzie tą samą drogą co
przycisk Stop: anuluje fade, kończy przejście i zeruje jasność. Usunięcie
innego wiersza tylko przesuwa wskaźnik; filtr nie ma znaczenia, bo sesja
pracuje na wierszach modelu źródłowego.

Weryfikacja: `pytest` — 84 zielone, `ruff check .` czysto; harness na prawdziwym
VLC: WAV `Playing` → `Stopped`, MP4 `Playing` → `Stopped`; usunięcie innego
wiersza przy aktywnym filtrze nie rusza playbacku; usunięcie w trakcie fade'a
anuluje fade i kończy przejście. Do potwierdzenia na sprzęcie: znikający obraz
i dźwięk na projekcji.
