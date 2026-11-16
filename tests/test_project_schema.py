"""Schemat pliku projektu: format bieżący, legacy i serializacja. Bez Qt i VLC."""

from showcontrol.domain.project_schema import (Project, ProjectItem,
                                               project_from_data, project_to_data)


def test_bare_list_is_legacy_format():
    project = project_from_data(["a.mp4", "b.mp3"])
    assert project == Project((ProjectItem("a.mp4"), ProjectItem("b.mp3")))
    assert project.overlay_path is None
    assert project.items[0].overlay is False
    assert project.items[0].overlay_path is None


def test_dict_format_reads_files_and_global_overlay():
    data = {
        "files": [{"path": "a.mp4", "overlay": True, "overlay_path": "item.png"}],
        "logo": "global.png",
    }
    project = project_from_data(data)
    assert project.items == (ProjectItem("a.mp4", True, "item.png"),)
    assert project.overlay_path == "global.png"


def test_mixed_list_supports_strings_and_dicts():
    project = project_from_data([
        "legacy.mp4",
        {"path": "new.mp4", "overlay": True, "overlay_path": "item.png"},
    ])
    assert project.items[0] == ProjectItem("legacy.mp4", False, None)
    assert project.items[1] == ProjectItem("new.mp4", True, "item.png")


def test_item_defaults_when_keys_are_missing():
    project = project_from_data({"files": [{"path": "a.mp4"}]})
    assert project.items[0].overlay is False
    assert project.items[0].overlay_path is None


def test_item_without_path_becomes_empty_string():
    project = project_from_data({"files": [{"overlay": True}]})
    assert project.items[0].path == ""
    assert project.items[0].overlay is True


def test_empty_dict_gives_empty_project():
    project = project_from_data({})
    assert project.items == ()
    assert project.overlay_path is None


def test_unknown_root_type_gives_empty_project():
    assert project_from_data("nie-projekt") == Project(())
    assert project_from_data(42) == Project(())


def test_project_to_data_has_v072_shape():
    project = Project(
        items=(ProjectItem("a.mp4", True, "item.png"), ProjectItem("b.mp3")),
        overlay_path="global.png",
    )
    assert project_to_data(project) == {
        "files": [
            {"path": "a.mp4", "overlay": True, "overlay_path": "item.png"},
            {"path": "b.mp3", "overlay": False, "overlay_path": None},
        ],
        "logo": "global.png",
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
    assert "logo" in data
