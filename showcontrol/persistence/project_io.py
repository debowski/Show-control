"""Zapis i odczyt projektu JSON zgodnego z `domain/project_schema.py`."""

from __future__ import annotations

import json

from showcontrol.domain.project_schema import ProjectFileError, project_from_data, project_to_data, validate_project_data


def save_project_file(path, project):
    """Zapisz obiekt `Project` do pliku JSON."""
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(project_to_data(project), handle, ensure_ascii=False, indent=4)


def load_project_file(path):
    """Wczytaj obiekt `Project` z pliku JSON.

    Błędy zawartości zgłaszane są jako `ProjectFileError` z nazwą problemu
    i szczegółami pola, żeby UI mogło pokazać komunikat po ludzku. Błędy
    wejścia/wyjścia (brak pliku, brak uprawnień) lecą dalej jako `OSError`.
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except UnicodeDecodeError as error:
        raise ProjectFileError("encoding") from error
    except json.JSONDecodeError as error:
        raise ProjectFileError("invalid_json", line=error.lineno, column=error.colno) from error

    validate_project_data(data)
    return project_from_data(data)


def partition_project_items(project, path_exists):
    """Dzieli pozycje projektu na istniejące i brakujące, w kolejności zapisu.

    Predykat istnienia pliku jest wstrzykiwany, żeby kolejność pozycji dało się
    sprawdzić bez dysku.
    """
    existing = []
    missing = []
    for item in project.items:
        (existing if path_exists(item.path) else missing).append(item)
    return tuple(existing), tuple(missing)
