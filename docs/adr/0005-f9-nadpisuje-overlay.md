# ADR 0005 — F9 nadpisuje overlay pozycji; checkbox pozycji znaczy „własny overlay"

**Status:** przyjęta
**Data:** 2026-11-13
**Kontekst:** `docs/refactor-plan.md` faza 3; `GLOSSARY.md`; ADR 0002

## Kontekst

Obecny kod łączy trzy źródła trybu projekcji alternatywą, nie priorytetem:

```python
show_overlay = global_overlay or item_overlay or show_audio_logo   # main.py:1746
```

Skutek: przycisk F9 **nie potrafi ukryć** overlaya przypisanego do pozycji.
Może tylko dodać overlay globalny tam, gdzie overlaya nie ma. Operator
obsługujący wydarzenie oczekuje czegoś przeciwnego — F9 ma być bezpiecznym
„zasłoń, co leci, i pokaż branding".

Do tego checkbox pozycji znaczy dziś dwie rzeczy naraz (ADR 0002 nazywa to
długiem): „ta pozycja używa overlaya" oraz „użyj dla niej overlaya globalnego",
gdy nie ma własnego assetu.

## Decyzja

### F9 — „Wymuś overlay"

F9 jest **stanem**, nie zdarzeniem: włączony obowiązuje do momentu wyłączenia
przez operatora, niezależnie od tego, ile pozycji przewinie się w międzyczasie.
Gdy jest włączony, projekcja pokazuje **overlay globalny** (wybrany przez
`select overlay file`) i zasłania zarówno media, jak i overlay bieżącej pozycji.

Po wyłączeniu natychmiast wraca to, co wynika z pozycji.

Gdy overlay globalny nie jest ustawiony, kontrolka jest **wyszarzona
i nieaktywna** z tooltipem. Kontrolka, która nic nie robi, jest mniejszym
ryzykiem niż kontrolka, która robi coś nieoczekiwanego.

F9 **nie jest zapisywany w projekcie** i jest zerowany przy starcie aplikacji
oraz przy wczytywaniu projektu. Nadpisanie żyje w obrębie sesji operatorskiej;
stan, który przeżywa restart, to nie nadpisanie, tylko pułapka.

### Checkbox pozycji

Checkbox pozycji znaczy wyłącznie **„ta pozycja używa swojego overlaya"**.
Nie ma już znaczenia „użyj globalnego". Bez własnego assetu checkbox jest
nieaktywny — nie ma czego pokazać.

### Precedencja

| Stan | Projekcja pokazuje |
|---|---|
| F9 włączony | overlay globalny |
| F9 wyłączony, pozycja ma włączony overlay + asset | asset pozycji |
| F9 wyłączony, pozycja audio + F10 | overlay globalny |
| inaczej | media |

F10 („overlay przy audio") zostaje bez zmian i działa tylko przy wyłączonym F9.

### Migracja starych projektów

Pozycje z `"overlay": true` i `"overlay_path": null` znaczyły dotąd „pokaż
overlay globalny". Przy wczytaniu **flaga jest czyszczona**, a operator dostaje
jednorazowy komunikat, że pozycja nie ma już overlaya. Projekt zapisuje się
w nowym kształcie dopiero, gdy operator sam zapisze.

## Konsekwencje

**Pozytywne**

- F9 robi dokładnie to, czego oczekuje operator w najgorszym momencie
  wydarzenia: zasłania wszystko jednym klawiszem.
- Checkbox przestaje mieć dwa znaczenia — znika dług z ADR 0002.
- „Użyj globalnego dla tej pozycji" znika jako osobny przypadek, bo zastępuje
  go F9. Model traci jeden bit semantyki.
- `set_overlay_path` przestaje sprzęgać asset z flagą (`main.py:846–848`).

**Negatywne**

- **To zmiana zachowania widoczna dla operatora**, więc zasada 1 planu
  („zachowanie bez zmian poza fazą 0") dostaje wyjątek, a faza 3 potrzebuje
  własnej bramy. Wersja przy wydaniu: minor, nie patch.
- Istniejące projekty zmieniają znaczenie; pozycje opierające się na globalnym
  overlayu przestaną go pokazywać.
- Operator musi pamiętać, że F9 jest włączony. Mitygacja: widoczny stan
  i oznaczenie przesłoniętych wierszy na playliście.

## Odrzucone alternatywy

**Zostawić logikę OR** — czyli F9 jako „dodaj", nie „nadpisz". Nie spełnia
oczekiwania „zasłoń wszystko".

**F9 jako przytrzymanie klawisza** — niepraktyczne przy utworze trwającym
kilka minut.

**Materializacja globalnego assetu do pozycji przy wczytaniu** (opcja Q1a) —
zachowuje stare zachowanie, ale podmienia dane operatora bez jego wiedzy.
Jednorazowy komunikat jest uczciwszy.

**Zapisywanie F9 w projekcie** — aplikacja startowałaby z brandingiem zamiast
pierwszej pozycji, a operator nie wybrał tego w tej sesji.

**F9 pokazujący czerń przy braku assetu** — sensowna funkcja sceniczna
(„kurtyna"), ale to nowa funkcja, nie refaktor. Zapisane jako pomysł na fazę B.
