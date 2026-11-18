"""Schemat pliku projektu. Bez Qt i bez VLC."""

from dataclasses import dataclass


class ProjectFileError(ValueError):
    """Nieprawidłowy plik projektu.

    `key` nazywa problem, a `params` niesie szczegóły (pole, indeks, typ).
    UI tłumaczy je na język operatora; domena nie zna języka interfejsu.
    """

    def __init__(self, key, **params):
        self.key = key
        self.params = params
        super().__init__(key)


@dataclass(frozen=True)
class ProjectItem:
    path: str
    overlay: bool = False
    overlay_path: str | None = None


@dataclass(frozen=True)
class Project:
    items: tuple
    overlay_path: str | None = None
    migrated_overlay_count: int = 0


def project_from_data(data):
    """Czyta projekt z JSON-a. Obsługuje format listy (legacy) i słownika.

    Elementy listy mogą być stringami (legacy) albo słownikami. Funkcja jest
    tolerancyjna: dane bez `path` dostają pustą ścieżkę, a nieznany typ główny
    daje pusty projekt. Pliki z dysku przechodzą najpierw przez
    `validate_project_data`, więc operator dostaje `ProjectFileError`
    ze wskazaniem pola zamiast cichego, zniekształconego projektu.

    Migracja ADR 0005: pozycja z `overlay: true` bez `overlay_path` traci flagę,
    bo checkbox znaczy teraz wyłącznie „używa własnego assetu".
    """
    if isinstance(data, list):
        raw_items = data
        overlay_path = None
    elif isinstance(data, dict):
        raw_items = data.get("files", [])
        overlay_path = data.get("overlay", data.get("logo", None))
    else:
        raw_items = []
        overlay_path = None

    items = []
    migrated_overlay_count = 0
    for raw in raw_items:
        if isinstance(raw, str):
            items.append(ProjectItem(raw))
        else:
            overlay = raw.get("overlay", False)
            item_overlay_path = raw.get("overlay_path", None)
            if overlay and not item_overlay_path:
                overlay = False
                migrated_overlay_count += 1
            items.append(ProjectItem(raw.get("path", ""), overlay, item_overlay_path))
    return Project(tuple(items), overlay_path, migrated_overlay_count)


def _json_type_name(value):
    """Nazwa typu w terminach JSON-a, żeby komunikat był zrozumiały dla operatora."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _validate_item(raw, index):
    if isinstance(raw, str):
        return
    if not isinstance(raw, dict):
        raise ProjectFileError("item_type", index=index, actual=_json_type_name(raw))
    if "path" not in raw:
        raise ProjectFileError("item_path_missing", index=index)
    if not isinstance(raw["path"], str):
        raise ProjectFileError("item_path_type", index=index, actual=_json_type_name(raw["path"]))
    if "overlay" in raw and not isinstance(raw["overlay"], bool):
        raise ProjectFileError("item_overlay_type", index=index, actual=_json_type_name(raw["overlay"]))
    overlay_path = raw.get("overlay_path")
    if overlay_path is not None and not isinstance(overlay_path, str):
        raise ProjectFileError("item_overlay_path_type", index=index, actual=_json_type_name(overlay_path))


def validate_project_data(data):
    """Sprawdza kształt danych projektu i wskazuje pierwsze nieprawidłowe pole.

    Format listy (legacy) i słownika są dopuszczalne. Wymagane pole `files`
    musi istnieć i być listą; każda pozycja to tekst albo obiekt z tekstowym
    `path`. Błędy zgłasza jako `ProjectFileError` z nazwą problemu i szczegółami.
    """
    if isinstance(data, list):
        raw_items = data
    elif isinstance(data, dict):
        if "files" not in data:
            raise ProjectFileError("missing_files")
        raw_items = data["files"]
        if not isinstance(raw_items, list):
            raise ProjectFileError("files_type", actual=_json_type_name(raw_items))
        field = "overlay" if "overlay" in data else "logo" if "logo" in data else None
        if field is not None:
            overlay = data[field]
            if overlay is not None and not isinstance(overlay, str):
                raise ProjectFileError("overlay_type", field=field, actual=_json_type_name(overlay))
    else:
        raise ProjectFileError("root_type", actual=_json_type_name(data))

    for index, raw in enumerate(raw_items, start=1):
        _validate_item(raw, index)


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
        "overlay": project.overlay_path,
    }
