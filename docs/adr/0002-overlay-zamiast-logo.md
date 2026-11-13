# ADR 0002 — „Overlay" zamiast „logo", jedna semantyka

**Status:** przyjęta
**Data:** 2026-11-13
**Kontekst:** `docs/refactor-plan.md`, fazy 1 i 3; `GLOSSARY.md`

## Kontekst

Słowo „logo" znaczy dziś trzy różne rzeczy:

| Znaczenie | Kod (`v0.7.1`) |
|---|---|
| globalny asset wyświetlany zamiast medium | `_logo_path`, `select_logo`, `update_logo_media` |
| per-item asset nadpisujący globalny | `overlay_path`, `set_overlay_path` |
| widżet rysujący asset | `LogoViewer` |
| tryb projekcji, w którym widać asset | `set_mode_audio` |
| zachowanie „pokaż obraz przy audio" | `logo_audio_checkbox`, F10 |

Do tego sam checkbox `logo_overlay_btn` znaczy jednocześnie „włącz overlay"
i „ta pozycja ma własny overlay". Precedencja istnieje wyłącznie w kodzie
`_set_projection_mode_for_path` (`main.py:1736–1759`) i tylko jedna osoba
wie, jaka jest.

Przy solowym utrzymaniu koszt tego jest mierzalny: przy każdym bugu pierwsze
10 minut idzie na ustalenie, o czym mowa, a nie na naprawę.

## Decyzja

Termin **„logo" przestaje być terminem domenowym**. Zostają trzy nazwy:

- **`overlay`** — globalny asset,
- **`item overlay`** — asset przypisany do pozycji,
- **`overlay on audio`** — zachowanie przy pozycji audio (dawniej
  „image for audio").

Zmiany nazw w kodzie:

| Było | Jest |
|---|---|
| `LogoViewer` | `OverlayViewer` |
| `set_mode_audio()` | `set_mode_overlay()` |
| `_logo_path` | `overlay_path` (globalny) |
| `logo_player` | `overlay_player` |
| `logo_audio_checkbox` | `overlay_on_audio_checkbox` |
| `toggle_logo_overlay` | `toggle_overlay` |
| `update_logo_visibility` | `update_overlay_visibility` |

Reguła precedencji wychodzi z `App` do `domain/overlay_rules.py` jako **czysta
funkcja**, testowana bez Qt i bez VLC.

## Konsekwencje

**Pozytywne**

- Jedno słowo = jedno pojęcie; nazwa modułu (`playback/overlay.py`) i funkcji
  (`domain/overlay_rules.py`) mówi to samo co glosariusz.
- Precedencja staje się testowalna — dziś jest nie do sprawdzenia bez
  uruchomienia aplikacji.
- Znikają dwa niemal identyczne bloki ładowania assetu
  (`_load_overlay_media` 1761–1792 vs `update_logo_media` 1977–2010).

**Negatywne**

- Duży, mechaniczny diff nazw — musi być **osobnym commitem** od zmian
  logicznych, inaczej recenzja jest niemożliwa.
- README mówi „logo" w kilku miejscach; wymaga przeglądu językowego.

## Ryzyko przy realizacji

Jeśli `_set_projection_mode_for_path` zachowuje się inaczej niż lista
precedencji w `GLOSSARY.md`, **wygrywa implementacja**, a lista jest
poprawiana. Różnica musi być zapisana w commicie. Kod jest źródłem prawdy
o zachowaniu; dokument jest źródłem prawdy o nazwach.
