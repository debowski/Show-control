"""Schemat pliku projektu: format bieżący, legacy i serializacja. Bez Qt i VLC."""

import pytest

from showcontrol.domain.project_schema import (
    Project,
    ProjectFileError,
    ProjectItem,
    project_from_data,
    project_to_data,
    validate_project_data,
)


def test_bare_list_is_legacy_format():
    project = project_from_data(["a.mp4", "b.mp3"])
    assert project == Project((ProjectItem("a.mp4"), ProjectItem("b.mp3")))
    assert project.overlay_path is None
    assert project.items[0].overlay is False
    assert project.items[0].overlay_path is None


def test_dict_format_reads_files_and_global_overlay():
    data = {
        "files": [{"path": "a.mp4", "overlay": True, "overlay_path": "item.png"}],
        "overlay": "global.png",
    }
    project = project_from_data(data)
    assert project.items == (ProjectItem("a.mp4", True, "item.png"),)
    assert project.overlay_path == "global.png"


def test_legacy_logo_key_still_reads_for_backward_compatibility():
    project = project_from_data(
        {
            "files": [{"path": "a.mp4"}],
            "logo": "legacy.png",
        }
    )
    assert project.overlay_path == "legacy.png"


def test_mixed_list_supports_strings_and_dicts():
    project = project_from_data(
        [
            "legacy.mp4",
            {"path": "new.mp4", "overlay": True, "overlay_path": "item.png"},
        ]
    )
    assert project.items[0] == ProjectItem("legacy.mp4", False, None)
    assert project.items[1] == ProjectItem("new.mp4", True, "item.png")


def test_item_defaults_when_keys_are_missing():
    project = project_from_data({"files": [{"path": "a.mp4"}]})
    assert project.items[0].overlay is False
    assert project.items[0].overlay_path is None


def test_item_without_path_becomes_empty_string_and_loses_orphan_overlay_flag():
    project = project_from_data({"files": [{"overlay": True}]})
    assert project.items[0].path == ""
    assert project.items[0].overlay is False
    assert project.migrated_overlay_count == 1


def test_orphan_overlay_flag_is_cleared_and_counted():
    project = project_from_data(
        {
            "files": [
                {"path": "a.mp4", "overlay": True, "overlay_path": None},
                {"path": "b.mp4", "overlay": False, "overlay_path": None},
                {"path": "c.mp4", "overlay": True, "overlay_path": "item.png"},
            ]
        }
    )
    assert [item.overlay for item in project.items] == [False, False, True]
    assert project.migrated_overlay_count == 1


def test_item_with_overlay_path_keeps_flag():
    project = project_from_data({"files": [{"path": "a.mp4", "overlay": True, "overlay_path": "item.png"}]})
    assert project.items[0].overlay is True
    assert project.migrated_overlay_count == 0


def test_empty_dict_gives_empty_project():
    project = project_from_data({})
    assert project.items == ()
    assert project.overlay_path is None


def test_unknown_root_type_gives_empty_project():
    assert project_from_data("nie-projekt") == Project(())
    assert project_from_data(42) == Project(())


def test_project_to_data_has_overlay_shape():
    project = Project(
        items=(ProjectItem("a.mp4", True, "item.png"), ProjectItem("b.mp3")),
        overlay_path="global.png",
    )
    assert project_to_data(project) == {
        "files": [
            {"path": "a.mp4", "overlay": True, "overlay_path": "item.png"},
            {"path": "b.mp3", "overlay": False, "overlay_path": None},
        ],
        "overlay": "global.png",
    }


def test_project_to_data_preserves_item_order():
    project = Project((ProjectItem("c"), ProjectItem("a"), ProjectItem("b")))
    assert [item["path"] for item in project_to_data(project)["files"]] == ["c", "a", "b"]


def test_round_trip_without_global_overlay():
    project = Project((ProjectItem("a.mp4", False, None),))
    assert project_from_data(project_to_data(project)) == project


def test_round_trip_with_global_overlay():
    project = Project((ProjectItem("a.mp4", True, "item.png"),), overlay_path="global.png")
    assert project_from_data(project_to_data(project)) == project


def test_round_trip_legacy_list_gets_new_shape():
    project = project_from_data(["a.mp4"])
    data = project_to_data(project)
    assert isinstance(data, dict)
    assert "files" in data
    assert "overlay" in data


def test_validate_accepts_current_shape():
    validate_project_data(
        {
            "files": [
                {"path": "a.mp4", "overlay": True, "overlay_path": "item.png"},
                {"path": "b.mp3", "overlay": False, "overlay_path": None},
            ],
            "overlay": "global.png",
        }
    )


def test_validate_accepts_legacy_list_and_logo_key():
    validate_project_data(["a.mp4", {"path": "b.mp3"}])
    validate_project_data({"files": [], "logo": None})


@pytest.mark.parametrize(
    ("data", "key", "params"),
    [
        ("nie-projekt", "root_type", {"actual": "string"}),
        ({}, "missing_files", {}),
        ({"files": "a.mp4"}, "files_type", {"actual": "string"}),
        ({"files": [42]}, "item_type", {"index": 1, "actual": "number"}),
        ({"files": [{"overlay": True}]}, "item_path_missing", {"index": 1}),
        ({"files": [{"path": 5}]}, "item_path_type", {"index": 1, "actual": "number"}),
        (
            {"files": [{"path": "a.mp4", "overlay": "tak"}]},
            "item_overlay_type",
            {"index": 1, "actual": "string"},
        ),
        (
            {"files": [{"path": "a.mp4", "overlay_path": 3}]},
            "item_overlay_path_type",
            {"index": 1, "actual": "number"},
        ),
        ({"files": [], "overlay": 3}, "overlay_type", {"field": "overlay", "actual": "number"}),
        ({"files": [], "logo": 3}, "overlay_type", {"field": "logo", "actual": "number"}),
    ],
)
def test_validate_points_at_the_bad_field(data, key, params):
    with pytest.raises(ProjectFileError) as info:
        validate_project_data(data)

    assert info.value.key == key
    assert info.value.params == params
