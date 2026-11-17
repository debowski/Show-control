# Dokumentacja domeny

Jak skille mają czytać dokumentację domenową tego repo.

## Przed eksploracją przeczytaj

- `GLOSSARY.md` w rootcie
- `docs/adr/` — ADR-y dotyczące obszaru, w którym pracujesz

Brak pliku nie jest błędem: nie zgłaszaj go i nie proponuj tworzenia z góry.
`/domain-modeling` tworzy je leniwie, gdy terminy lub decyzje faktycznie
zostaną rozstrzygnięte.

## Układ: single-context

`GLOSSARY.md` + `docs/adr/` w rootcie. Brak `GLOSSARY-MAP.md`.

## Używaj słownictwa glosariusza

Nazwy pojęć w tytułach ticketów, propozycjach refaktoru, hipotezach i testach
biorą się z `GLOSSARY.md`. Nie dryfuj do synonimów, których glosariusz
unika. Brak pojęcia = sygnał: albo wymyślasz język, którego projekt nie używa,
albo jest realna luka (do `/domain-modeling`).

## Zgłaszaj konflikty z ADR

Jeśli wynik pracy przeczy istniejącemu ADR, powiedz to wprost, zamiast go
po cichu nadpisywać:

> _Sprzeczne z ADR-0004 (fade 0–1 s), ale warto otworzyć, bo…_
