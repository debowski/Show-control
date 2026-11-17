# 07: Dialog dodawania przyjmuje wszystkie obsługiwane formaty

**What to build:** Filtr w dialogu dodawania mediów pokazuje i przyjmuje
wszystkie formaty, które aplikacja faktycznie obsługuje — łącznie z dźwiękiem
(`.wav`, `.flac`, `.aac`, `.ogg`, `.m4a`) i obrazami (`.jpeg`, `.bmp`, `.gif`).
Dziś operator nie widzi tych plików w dialogu, choć odtwarzanie by je przyjęło.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Filtr dialogu zawiera wszystkie obsługiwane rozszerzenia mediów
- [ ] Pliki `.wav`, `.flac`, `.aac`, `.ogg`, `.m4a` są widoczne i wybieralne
- [ ] Pliki `.jpeg`, `.bmp`, `.gif` są widoczne i wybieralne
- [ ] Lista rozszerzeń ma jedno źródło wspólne z walidacją odtwarzania
