"""Magazyn pozycji playlisty — dane i operacje na wierszach. Bez Qt."""

import os
from dataclasses import dataclass


@dataclass
class PlaylistEntry:
    path: str
    filename: str
    overlay: bool = False
    overlay_path: str | None = None


class PlaylistStore:
    """Właściciel wierszy playlisty i wskaźnika odtwarzanej pozycji."""

    def __init__(self):
        self._entries: list[PlaylistEntry] = []
        self.playing_row = -1

    def rows(self):
        return tuple(self._entries)

    def row_count(self):
        return len(self._entries)

    def entry_at(self, row):
        return self._entries[row]

    def path_at(self, row):
        return self._entries[row].path

    def file_paths(self):
        return [entry.path for entry in self._entries]

    def row_for_path(self, path):
        for row, entry in enumerate(self._entries):
            if entry.path == path:
                return row
        return -1

    @staticmethod
    def _entry_for(path):
        return PlaylistEntry(path=path, filename=os.path.basename(path))

    def insert_blanks(self, row, count):
        entries = [self._entry_for('') for _ in range(count)]
        self._entries[row:row] = entries
        if self.playing_row >= row:
            self.playing_row += count

    def add(self, paths, row=None):
        insert_row = self.row_count() if row is None or row == -1 else row
        entries = [self._entry_for(path) for path in paths]
        self._entries[insert_row:insert_row] = entries
        if self.playing_row >= insert_row:
            self.playing_row += len(entries)
        return insert_row

    def remove(self, row, count):
        del self._entries[row:row + count]
        if self.playing_row >= row and self.playing_row < row + count:
            self.playing_row = -1
        elif self.playing_row >= row + count:
            self.playing_row -= count

    def clear(self):
        self._entries = []
        self.playing_row = -1

    def can_move(self, source_row, count, destination_child):
        return not (source_row == destination_child
                    or source_row == destination_child - 1)

    def move(self, source_row, count, destination_child):
        items = self._entries[source_row:source_row + count]
        del self._entries[source_row:source_row + count]

        insert_row = destination_child
        if source_row < destination_child:
            insert_row -= count

        self._entries[insert_row:insert_row] = items
        self._update_playing_row_on_move(source_row, count, destination_child, insert_row)
        return insert_row

    def _update_playing_row_on_move(self, source_row, count, destination_child, insert_row):
        if source_row <= self.playing_row < source_row + count:
            offset = self.playing_row - source_row
            self.playing_row = insert_row + offset
        else:
            if source_row < self.playing_row and destination_child > self.playing_row:
                self.playing_row -= count
            elif source_row > self.playing_row and destination_child <= self.playing_row:
                self.playing_row += count

    def set_playing_row(self, row):
        old_row = self.playing_row
        self.playing_row = row
        return old_row

    def overlay_for_row(self, row):
        if 0 <= row < len(self._entries):
            return self._entries[row].overlay
        return False

    def overlay_path_for_row(self, row):
        if 0 <= row < len(self._entries):
            return self._entries[row].overlay_path
        return None

    def set_overlay(self, row, enabled):
        if 0 <= row < len(self._entries):
            self._entries[row].overlay = enabled

    def set_overlay_path(self, row, path):
        if 0 <= row < len(self._entries):
            self._entries[row].overlay_path = path
            self._entries[row].overlay = bool(path)

    def set_overlay_state(self, row, overlay, overlay_path):
        if 0 <= row < len(self._entries):
            self._entries[row].overlay = overlay
            self._entries[row].overlay_path = overlay_path
