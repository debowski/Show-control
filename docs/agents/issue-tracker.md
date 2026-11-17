# Issue tracker: lokalny markdown

Tickety i spece tego repo żyją jako pliki markdown w `.scratch/`.

## Konwencje

- Jedna funkcja = jeden katalog: `.scratch/<feature-slug>/`
- Spec: `.scratch/<feature-slug>/spec.md`
- Tickety implementacyjne: jeden plik na ticket,
  `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numeracja od `01`,
  nigdy jeden wspólny plik
- Stan triage: linia `Status:` blisko góry pliku (wartości w
  `triage-labels.md`)
- Komentarze i historia: dopisywane na dole pod nagłówkiem `## Comments`

## Gdy skill mówi „publish to the issue tracker"

Utwórz nowy plik w `.scratch/<feature-slug>/` (tworząc katalog, jeśli trzeba).

## Gdy skill mówi „fetch the relevant ticket"

Przeczytaj plik pod wskazaną ścieżką. Użytkownik zwykle poda ścieżkę lub numer.

## Wayfinding

- **Mapa**: `.scratch/<effort>/map.md` (notatki, decyzje, mgła)
- **Ticket-dziecko**: `.scratch/<effort>/issues/NN-<slug>.md`, z linią
  `Type:` (`research`/`prototype`/`grilling`/`task`) i `Status:`
  (`claimed`/`resolved`)
- **Blokady**: linia `Blocked by: NN, NN` blisko góry; ticket jest
  odblokowany, gdy wszystkie wymienione pliki są `resolved`
- **Frontier**: otwarte, nieodblokowane i nieprzypisane pliki w
  `.scratch/<effort>/issues/`, wygrywa najniższy numer
- **Claim**: ustaw `Status: claimed` i zapisz przed pracą
- **Resolve**: dopisz odpowiedź pod `## Answer`, ustaw `Status: resolved`,
  dopisz wskaźnik kontekstu do `map.md`
