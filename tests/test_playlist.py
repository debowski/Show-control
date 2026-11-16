"""Operacje na wierszach playlisty i reguły przesunięcia indeksu. Bez Qt i VLC."""

import sys

from showcontrol.domain.playlist import (PlaylistEntry, PlaylistStore,
                                         adjust_row_for_insert,
                                         adjust_row_for_move,
                                         adjust_row_for_remove)


def _store(*paths):
    store = PlaylistStore()
    store.add(list(paths))
    return store


def test_add_to_empty_store():
    store = PlaylistStore()
    assert store.add(["a.mp4"]) == 0
    assert store.row_count() == 1
    assert store.path_at(0) == "a.mp4"


def test_add_returns_insert_row_and_appends_at_end():
    store = _store("a.mp4")
    assert store.add(["b.mp3"]) == 1
    assert store.path_at(1) == "b.mp3"


def test_add_at_row_inserts_in_the_middle():
    store = _store("a.mp4", "c.mp4")
    assert store.add(["b.mp3"], row=1) == 1
    assert [entry.path for entry in store.rows()] == ["a.mp4", "b.mp3", "c.mp4"]


def test_add_uses_filename_from_path():
    store = _store("katalog\\utwor.mp3")
    assert store.entry_at(0).filename == "utwor.mp3"


def test_insert_blanks_adds_empty_entries():
    store = _store("a.mp4")
    store.insert_blanks(0, 2)
    assert store.row_count() == 3
    assert [entry.path for entry in store.rows()] == ["", "", "a.mp4"]


def test_can_move_rejects_no_op_destinations():
    store = _store("a.mp4", "b.mp4")
    assert store.can_move(0, 1, 0) is False
    assert store.can_move(0, 1, 1) is False
    assert store.can_move(0, 1, 2) is True


def test_move_down_reorders_entries():
    store = _store("a.mp4", "b.mp4", "c.mp4")
    insert_row = store.move(0, 1, 2)
    assert insert_row == 1
    assert [entry.path for entry in store.rows()] == ["b.mp4", "a.mp4", "c.mp4"]


def test_move_up_reorders_entries():
    store = _store("a.mp4", "b.mp4", "c.mp4")
    insert_row = store.move(2, 1, 0)
    assert insert_row == 0
    assert [entry.path for entry in store.rows()] == ["c.mp4", "a.mp4", "b.mp4"]


def test_store_does_not_own_playing_row():
    store = PlaylistStore()
    assert not hasattr(store, "playing_row")
    assert not hasattr(store, "set_playing_row")


def test_adjust_for_insert_before_playing_row():
    assert adjust_row_for_insert(1, 0, 1) == 2


def test_adjust_for_insert_at_playing_row():
    assert adjust_row_for_insert(1, 1, 1) == 2


def test_adjust_for_insert_after_playing_row():
    assert adjust_row_for_insert(1, 2, 1) == 1


def test_adjust_for_insert_without_playing_row():
    assert adjust_row_for_insert(-1, 0, 2) == -1


def test_adjust_for_insert_multiple_rows():
    assert adjust_row_for_insert(2, 0, 2) == 4


def test_adjust_for_remove_current_row_gives_minus_one():
    assert adjust_row_for_remove(1, 1, 1) == -1


def test_adjust_for_remove_range_containing_playing_row_gives_minus_one():
    assert adjust_row_for_remove(1, 0, 2) == -1


def test_adjust_for_remove_row_before_playing_row_shifts_it():
    assert adjust_row_for_remove(1, 0, 1) == 0


def test_adjust_for_remove_row_after_playing_row_keeps_it():
    assert adjust_row_for_remove(0, 1, 1) == 0


def test_adjust_for_remove_without_playing_row():
    assert adjust_row_for_remove(-1, 0, 1) == -1


def test_adjust_for_move_keeps_row_on_moved_entry_down():
    assert adjust_row_for_move(0, 0, 1, 3) == 2


def test_adjust_for_move_keeps_row_on_moved_entry_up():
    assert adjust_row_for_move(2, 2, 1, 0) == 0


def test_adjust_for_move_shifts_row_when_other_entry_moves_down():
    assert adjust_row_for_move(1, 0, 1, 3) == 0


def test_adjust_for_move_shifts_row_when_other_entry_moves_up():
    assert adjust_row_for_move(1, 2, 1, 0) == 2


def test_adjust_for_move_without_playing_row():
    assert adjust_row_for_move(-1, 0, 1, 3) == -1


def test_overlay_accessors_for_valid_and_invalid_rows():
    store = _store("a.mp4")
    assert store.overlay_for_row(0) is False
    assert store.overlay_path_for_row(0) is None
    assert store.overlay_for_row(5) is False
    assert store.overlay_path_for_row(-1) is None


def test_set_overlay_toggles_item_flag():
    store = _store("a.mp4")
    store.set_overlay(0, True)
    assert store.overlay_for_row(0) is True
    store.set_overlay(0, False)
    assert store.overlay_for_row(0) is False


def test_set_overlay_path_sets_flag_and_path():
    store = _store("a.mp4")
    store.set_overlay_path(0, "item.png")
    assert store.overlay_for_row(0) is True
    assert store.overlay_path_for_row(0) == "item.png"


def test_set_overlay_path_none_clears_flag():
    store = _store("a.mp4")
    store.set_overlay_path(0, "item.png")
    store.set_overlay_path(0, None)
    assert store.overlay_for_row(0) is False
    assert store.overlay_path_for_row(0) is None


def test_set_overlay_state_sets_flag_independently_of_path():
    store = _store("a.mp4")
    store.set_overlay_state(0, True, None)
    assert store.overlay_for_row(0) is True
    assert store.overlay_path_for_row(0) is None


def test_set_overlay_methods_ignore_out_of_range_rows():
    store = _store("a.mp4")
    store.set_overlay(3, True)
    store.set_overlay_path(3, "item.png")
    store.set_overlay_state(3, True, "item.png")
    assert store.rows() == (PlaylistEntry("a.mp4", "a.mp4"),)


def test_file_paths_returns_paths_in_order():
    store = _store("a.mp4", "b.mp3")
    assert store.file_paths() == ["a.mp4", "b.mp3"]


def test_row_for_path_returns_first_match_or_minus_one():
    store = _store("a.mp4", "b.mp3")
    assert store.row_for_path("b.mp3") == 1
    assert store.row_for_path("nie-ma.mp4") == -1


def test_rows_is_a_snapshot_tuple():
    store = _store("a.mp4")
    snapshot = store.rows()
    store.add(["b.mp4"])
    assert isinstance(snapshot, tuple)
    assert len(snapshot) == 1
    assert store.row_count() == 2


def test_clear_removes_entries():
    store = _store("a.mp4")
    store.clear()
    assert store.row_count() == 0


def test_domain_modules_do_not_import_qt_or_vlc():
    assert "PyQt6" not in sys.modules
    assert "vlc" not in sys.modules
