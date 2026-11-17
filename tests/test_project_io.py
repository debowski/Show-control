"""Zapis i odczyt projektu z pliku JSON. Bez Qt i VLC."""

import json

import pytest

from showcontrol.domain.project_schema import Project, ProjectItem
from showcontrol.persistence.project_io import load_project_file, save_project_file


def test_save_writes_new_overlay_shape(tmp_path):
    path = tmp_path / "projekt.json"
    project = Project(
        items=(
            ProjectItem("a.mp4", True, "item.png"),
            ProjectItem("b.mp3"),
        ),
        overlay_path="global.png",
    )

    save_project_file(path, project)

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data == {
        "files": [
            {"path": "a.mp4", "overlay": True, "overlay_path": "item.png"},
            {"path": "b.mp3", "overlay": False, "overlay_path": None},
        ],
        "overlay": "global.png",
    }
    assert "logo" not in data


def test_save_and_load_round_trip(tmp_path):
    path = tmp_path / "projekt.json"
    project = Project(
        items=(
            ProjectItem("a.mp4", True, "item.png"),
            ProjectItem("b.mp3", False, None),
        ),
        overlay_path="global.png",
    )

    save_project_file(path, project)

    assert load_project_file(path) == project


def test_project_without_overlay_keeps_no_overlay(tmp_path):
    path = tmp_path / "bez-overlaya.json"
    project = Project(
        items=(ProjectItem("a.mp4", False, None),),
        overlay_path=None,
    )

    save_project_file(path, project)

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["overlay"] is None
    assert load_project_file(path).overlay_path is None


def test_load_legacy_logo_key(tmp_path):
    path = tmp_path / "legacy.json"
    path.write_text(
        json.dumps(
            {
                "files": [{"path": "a.mp4"}],
                "logo": "stary.png",
            }
        ),
        encoding="utf-8",
    )

    project = load_project_file(path)

    assert project.overlay_path == "stary.png"
    assert project.items == (ProjectItem("a.mp4"),)


def test_load_bare_list(tmp_path):
    path = tmp_path / "legacy.json"
    path.write_text(json.dumps(["a.mp4", "b.mp3"]), encoding="utf-8")

    project = load_project_file(path)

    assert project == Project((ProjectItem("a.mp4"), ProjectItem("b.mp3")))


def test_load_mixed_legacy_list(tmp_path):
    path = tmp_path / "legacy.json"
    path.write_text(
        json.dumps(
            [
                "stary.mp4",
                {"path": "nowy.mp4", "overlay": True, "overlay_path": "item.png"},
            ]
        ),
        encoding="utf-8",
    )

    project = load_project_file(path)

    assert project.items == (
        ProjectItem("stary.mp4", False, None),
        ProjectItem("nowy.mp4", True, "item.png"),
    )


def test_load_migrates_orphan_overlay_flag(tmp_path):
    path = tmp_path / "legacy.json"
    path.write_text(
        json.dumps(
            {
                "files": [
                    {"path": "a.mp4", "overlay": True, "overlay_path": None},
                    {"path": "b.mp4", "overlay": True, "overlay_path": "item.png"},
                ],
            }
        ),
        encoding="utf-8",
    )

    project = load_project_file(path)

    assert [item.overlay for item in project.items] == [False, True]
    assert project.migrated_overlay_count == 1


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_project_file(tmp_path / "nie-ma.json")


def test_load_invalid_json_raises(tmp_path):
    path = tmp_path / "uszkodzony.json"
    path.write_text("{nie-json", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        load_project_file(path)
