"""Zapis i odczyt projektu z pliku JSON. Bez Qt i VLC."""

import json

import pytest

from showcontrol.domain.project_schema import Project, ProjectFileError, ProjectItem
from showcontrol.persistence.project_io import load_project_file, partition_project_items, save_project_file


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


def test_round_trip_preserves_duplicates_order_and_per_row_overlays(tmp_path):
    path = tmp_path / "duplikaty.json"
    project = Project(
        items=(
            ProjectItem("a.mp4"),
            ProjectItem("a.mp4", True, "item.png"),
            ProjectItem("b.mp3"),
            ProjectItem("a.mp4", False, "inny.png"),
        ),
        overlay_path=None,
    )

    save_project_file(path, project)

    assert load_project_file(path) == project


def test_partition_project_items_keeps_order_and_splits_missing():
    project = Project(
        items=(
            ProjectItem("a.mp4"),
            ProjectItem("brak.mp4", True, "brak.png"),
            ProjectItem("a.mp4", True, "item.png"),
        )
    )

    existing, missing = partition_project_items(project, lambda path: path != "brak.mp4")

    assert [item.path for item in existing] == ["a.mp4", "a.mp4"]
    assert [item.overlay_path for item in existing] == [None, "item.png"]
    assert [item.path for item in missing] == ["brak.mp4"]


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


def test_load_invalid_json_raises_readable_error(tmp_path):
    path = tmp_path / "uszkodzony.json"
    path.write_text("{nie-json", encoding="utf-8")

    with pytest.raises(ProjectFileError) as info:
        load_project_file(path)

    assert info.value.key == "invalid_json"
    assert info.value.params["line"] == 1
    assert info.value.params["column"] > 0


def test_load_non_utf8_file_raises_readable_error(tmp_path):
    path = tmp_path / "inne-kodowanie.json"
    path.write_bytes(b'{"files": ["za\xb9\xbf\xf3\xb3.mp4"]}')

    with pytest.raises(ProjectFileError) as info:
        load_project_file(path)

    assert info.value.key == "encoding"


def test_load_project_without_files_field_raises_readable_error(tmp_path):
    path = tmp_path / "niepelny.json"
    path.write_text(json.dumps({"overlay": "global.png"}), encoding="utf-8")

    with pytest.raises(ProjectFileError) as info:
        load_project_file(path)

    assert info.value.key == "missing_files"


def test_load_project_with_wrong_file_field_type_names_the_field(tmp_path):
    path = tmp_path / "zle-pole.json"
    path.write_text(json.dumps({"files": "a.mp4"}), encoding="utf-8")

    with pytest.raises(ProjectFileError) as info:
        load_project_file(path)

    assert info.value.key == "files_type"
    assert info.value.params == {"actual": "string"}
