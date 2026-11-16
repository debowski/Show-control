"""Schemat pliku projektu. Bez Qt i bez VLC."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectItem:
    path: str
    overlay: bool = False
    overlay_path: str | None = None


@dataclass(frozen=True)
class Project:
    items: tuple
    overlay_path: str | None = None


def project_from_data(data):
    """Czyta projekt z JSON-a. Obsługuje format listy (legacy) i słownika.

    Elementy listy mogą być stringami (legacy) albo słownikami. Zachowanie
    dla uszkodzonych danych jest takie jak w `v0.7.2`: element inny niż
    string/słownik powoduje wyjątek, który wołający pokazuje jako błąd odczytu.
    """
    if isinstance(data, list):
        raw_items = data
        overlay_path = None
    elif isinstance(data, dict):
        raw_items = data.get('files', [])
        overlay_path = data.get('logo', None)
    else:
        raw_items = []
        overlay_path = None

    items = []
    for raw in raw_items:
        if isinstance(raw, str):
            items.append(ProjectItem(raw))
        else:
            items.append(ProjectItem(
                raw.get('path', ''),
                raw.get('overlay', False),
                raw.get('overlay_path', None),
            ))
    return Project(tuple(items), overlay_path)


def project_to_data(project):
    """Serializuje projekt do kształtu zapisywanego przez `v0.7.2`."""
    return {
        "files": [
            {
                "path": item.path,
                "overlay": item.overlay,
                "overlay_path": item.overlay_path,
            }
            for item in project.items
        ],
        "logo": project.overlay_path,
    }
