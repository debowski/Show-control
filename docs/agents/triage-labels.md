# Etykiety triage

Skille mówią o pięciu kanonicznych rolach triage. Ten plik mapuje role na
konkretne wartości używane w tym repo.

| Rola w mattpocock/skills | Wartość u nas  | Znaczenie                                  |
| ------------------------ | -------------- | ------------------------------------------ |
| `needs-triage`           | `needs-triage` | Maintainer musi ocenić zgłoszenie          |
| `needs-info`             | `needs-info`   | Czekamy na informacje od zgłaszającego      |
| `ready-for-agent`        | `ready-for-agent` | W pełni wyspecyfikowane, gotowe dla agenta |
| `ready-for-human`        | `ready-for-human` | Wymaga pracy człowieka                   |
| `wontfix`                | `wontfix`      | Nie będzie realizowane                      |

Tracker jest lokalny (markdown), więc „etykieta" to wartość linii `Status:`
w pliku ticketu pod `.scratch/<feature>/issues/`. Gdy skill mówi o roli
(np. „apply the AFK-ready triage label"), wpisz odpowiadającą wartość z
tabeli. Zmieniając nazwy, edytuj kolumnę „Wartość u nas".
