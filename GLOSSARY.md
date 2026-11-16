# Glosariusz — Show Control

Terminy domenowe. Jeden termin = jedno znaczenie. Jeśli kod używa innej nazwy
niż ta tabela, to kod jest błędny, nie tabela.

Zasada: **„logo" nie jest terminem domenowym.** Zostało wycofane
(`docs/adr/0002-overlay-zamiast-logo.md`). Jeśli widzisz `logo` w kodzie
pisanym po fazie 3 refaktoru — to regresja nazewnictwa.

---

## Aktorzy i powierzchnie

**Operator** — człowiek obsługujący wydarzenie. Widzi wyłącznie konsolę.
Synonim w kodzie: `operator`. Nie „user", nie „klient".

**Konsola operatora** (`operator console`) — okno główne, `MainWindow`.
Jedyna powierzchnia, na którą operator ma patrzeć podczas wydarzenia.

**Okno projekcji** (`projection window`) — drugi top-level widget, pełny ekran
na drugim monitorze. Widzi je wyłącznie publiczność. Zamknięcie go **ukrywa**,
nie niszczy.

**Tryb projekcji** (`projection mode`) — co okno projekcji pokazuje w danej
chwili. Dwie wartości: `media` (bieżąca pozycja playlisty) i `overlay`
(asset overlay). Nie ma trybu trzeciego — „audio mode" to była nazwa trybu
overlay, gdy bieżąca pozycja jest plikiem audio.

---

## Playlista

**Pozycja playlisty** (`playlist item`) — jeden wpis: `filename`, `path`,
`overlay`, `overlay_path`. Nie „track" (to sugeruje tylko audio), nie „klip".

**Playlista** (`playlist`) — uporządkowana lista pozycji, jeden projekt = jedna
playlista. Kolejność jest znacząca: `next`/`previous` chodzą po niej liniowo.

**Odtwarzana pozycja** (`playing row` / `current item`) — pozycja wskazywana
przez sesję jako aktualna. Może być w stanie odtwarzania albo pauzy.

**Rodzaj medium** (`media kind`) — `video`, `audio` albo `image`. Klasyfikacja
po rozszerzeniu, nie po zawartości pliku. To jedyne miejsce, gdzie rozszerzenia
są znaczące: `domain/media.py`.

---

## Overlay

**Overlay** (`overlay`) — pojedynczy, globalny asset wyświetlany **zamiast**
bieżącej pozycji: obraz albo zapętlone wideo bez dźwięku. Wcześniej: „logo".

**Overlay pozycji** (`item overlay`) — asset przypisany do konkretnej pozycji.
Checkbox przy pozycji znaczy wyłącznie „ta pozycja używa swojego overlaya";
bez własnego assetu checkbox jest nieaktywny. Wcześniej: „per-item overlay",
„custom logo". Checkbox **nie** znaczy „użyj globalnego" — od tego jest F9.

**Overlay przy audio** (`overlay on audio`) — zachowanie: gdy bieżąca pozycja
jest plikiem audio, okno projekcji pokazuje overlay zamiast czerni.
Wcześniej: „image for audio".

**Nasycenie overlay** — nie istnieje. Jest jeden overlay na raz; nie ma
komponowania ani nakładania dwóch assetów.

### Precedencja

Rozstrzygana w jednym miejscu, `domain/overlay_rules.py`, jako czysta funkcja.
**To priorytet, nie alternatywa** — patrz `docs/adr/0005-f9-nadpisuje-overlay.md`.

| Stan | Projekcja pokazuje |
|---|---|
| F9 włączony | overlay globalny |
| F9 wyłączony, pozycja ma włączony overlay + własny asset | asset pozycji |
| F9 wyłączony, pozycja audio + F10 | overlay globalny |
| inaczej | media |

**F9 jest stanem, nie zdarzeniem.** Włączony obowiązuje do wyłączenia przez
operatora, niezależnie od liczby przewiniętych pozycji, i zasłania zarówno
media, jak i overlay bieżącej pozycji. Po wyłączeniu wraca natychmiast to,
co wynika z pozycji. F9 nie jest zapisywany w projekcie i jest zerowany przy
starcie oraz przy wczytywaniu projektu.

**Stan obecny:** kod implementuje tabelę powyżej od fazy 3 (ADR 0005).
Wcześniej (`v0.7.1`) warunki były alternatywą
(`show_overlay = global or item or on_audio`), więc F9 nie potrafił ukryć
overlaya pozycji. To była zmiana zachowania, nie przeniesienie — osobny
commit i osobna brama.

Przy braku assetu globalnego F9 jest wyszarzony i nieaktywny.

---

## Odtwarzanie

**Sesja odtwarzania** (`playback session`) — właściciel stanu „co teraz gra,
w jakim trybie, co dalej". Po fazie 4: `playback/session.py`. Jedyne miejsce
znające bieżącą pozycję.

**Silnik** (`engine`) — właściciel `vlc.Instance` i dwóch `MediaPlayer`
(główny + overlay). Nie zna playlisty ani projektu.

**Fade out** — kontrolowane wyciszenie i przyciemnienie przed zatrzymaniem
odtwarzania. Zakres 0–1.0 s, domyślnie 0.8 s
(`docs/adr/0004-fade-0-1s.md`). `0` = cięcie natychmiastowe.
Nie „crossfade" — nie ma przenikania między pozycjami.

**Blokada przejścia** (`transition guard`) — stan, w którym nowe polecenia
play/stop są ignorowane, bo trwa przejście. Dziś `is_transitioning`.

**Autoplay** — automatyczne przejście do następnej pozycji: obrazy po zadanym
czasie, wideo po zdarzeniu `Ended`. **Nie zawija** na końcu playlisty.

**Czas ekspozycji obrazu** (`image duration`) — ile sekund obraz jest widoczny
przy autoplay. 1–60 s. Nie „image speed" (to nazwa suwaka, nie pojęcia).

**Seeking** — ręczne przeciąganie pozycji w mediach; wstrzymuje aktualizację
paska postępu. Dziś `user_is_seeking`.

---

## Sterowanie

**Tryb pilota** (`remote mode`) — mapowanie nawigacji na strzałki
lewą/prawą zamiast górę/dół, dla pilotów prezentacyjnych.

**Skrót** (`shortcut`) — pojedyncze przypisanie klawisza do akcji.
Jedno źródło: `ui/shortcuts.py`. `shortcuts.json` zostało wycofane.

**Motyw** (`theme`) — jeden z czterech zestawów tokenów kolorów.
Token motywu musi być **użyty** — token zdefiniowany i nieużywany jest błędem
(dziś: `list_play`).

---

## Dane

**Projekt** (`project`) — plik JSON: playlista + overlay globalny. Nie zawiera
ustawień odtwarzania. Nie ma numeru wersji schematu — to dług do spłaty
w `domain/project_schema.py`.

**Ustawienie** (`setting`) — preferencja operatora trwała między uruchomieniami
(`QSettings`). Dziś tylko: motyw, język, ostatni projekt. Wszystko inne
(objętość, jasność, fade, autoplay, tryb pilota, czas obrazu) **nie jest**
ustawieniem i resetuje się przy starcie — do zmiany dopiero w fazie B.

**Wersja** (`version`) — jedno źródło: `showcontrol/__init__.py:__version__`.
Tag gita i nagłówek pliku nie są źródłami prawdy.
