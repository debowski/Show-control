"""Zapis i odczyt projektu JSON zgodnego z `domain/project_schema.py`."""

from __future__ import annotations

import json

from showcontrol.domain.project_schema import project_from_data, project_to_data


def save_project_file(path, project):
    """Zapisz obiekt `Project` do pliku JSON."""
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(project_to_data(project), handle, ensure_ascii=False, indent=4)


def load_project_file(path):
    """Wczytaj obiekt `Project` z pliku JSON."""
    with open(path, "r", encoding="utf-8") as handle:
        return project_from_data(json.load(handle))
