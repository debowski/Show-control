# 07: Dialog dodawania przyjmuje wszystkie obsługiwane formaty

**What to build:** Filtr w dialogu dodawania mediów pokazuje i przyjmuje
wszystkie formaty, które aplikacja faktycznie obsługuje — łącznie z dźwiękiem
(`.wav`, `.flac`, `.aac`, `.ogg`, `.m4a`) i obrazami (`.jpeg`, `.bmp`, `.gif`).
Dziś operator nie widzi tych plików w dialogu, choć odtwarzanie by je przyjęło.

**Blocked by:** None (can start immediately)

**Status:** ready-for-human

- [x] Filtr dialogu zawiera wszystkie obsługiwane rozszerzenia mediów
- [x] Pliki `.wav`, `.flac`, `.aac`, `.ogg`, `.m4a` są widoczne i wybieralne
- [x] Pliki `.jpeg`, `.bmp`, `.gif` są widoczne i wybieralne
- [x] Lista rozszerzeń ma jedno źródło wspólne z walidacją odtwarzania

## Comments

Realizacja: `domain/media.py` składa `MEDIA_EXTENSIONS` z list
`VIDEO_EXTENSIONS`, `AUDIO_EXTENSIONS` i `IMAGE_EXTENSIONS`; nie ma już
ręcznie utrzymywanej trzynastoelementowej listy obok list rodzajów. Filtr
dialogu dodawania mediów powstaje w `ui/i18n.py` z tych stałych
(`media_dialog_filter`), a `window.add_files` używa go zamiast tekstu z
`media_filter`. Filtr pokazuje teraz także `.wav`, `.flac`, `.aac`, `.ogg`,
`.m4a`, `.jpeg`, `.bmp` i `.gif`.

Przy okazji, za zgodą operatora, filtry overlaya (`overlay_filter`,
`overlay_item_filter`) korzystają z `IMAGE_EXTENSIONS`, `VIDEO_EXTENSIONS` i
`OVERLAY_EXTENSIONS` zamiast duplikować maski w tekstach PL/EN.

Weryfikacja: `pytest` — 93 zielone (nowe `tests/test_media.py` sprawdza
komplet formatów PL/EN, brak audio w filtrach overlaya i brak
niewypełnionych placeholderów), `ruff check .` czysto, okno główne
konstruuje się headless. Do potwierdzenia na sprzęcie: dialog „Dodaj
multimedia” pokazuje i pozwala wybrać pliki audio oraz `.jpeg`/`.bmp`/`.gif`.

