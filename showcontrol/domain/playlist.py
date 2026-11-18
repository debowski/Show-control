"""Magazyn pozycji playlisty — dane i operacje na wierszach. Bez Qt.

Wskaźnik odtwarzanej pozycji nie jest częścią magazynu: należy do
`playback/session.py`. Tutaj zostają tylko czyste reguły przesunięcia indeksu
przy zmianach wierszy, używane przez sesję.
"""

import os
from dataclasses import dataclass


def adjust_row_for_insert(playing_row, first, count):
    """Nowy indeks odtwarzanej pozycji po wstawieniu `count` wierszy w `first`."""
    if playing_row >= first:
        return playing_row + count
    return playing_row


def adjust_row_for_remove(playing_row, first, count):
    """Nowy indeks po usunięciu zakresu; usunięcie bieżącego wiersza daje -1."""
    last = first + count - 1
    if first <= playing_row <= last:
        return -1
    if playing_row > last:
        return playing_row - count
    return playing_row


def adjust_row_for_move(playing_row, source_row, count, destination_child):
    """Nowy indeks po przeniesieniu zakresu (semantyka `beginMoveRows`)."""
    insert_row = destination_child
    if source_row < destination_child:
        insert_row -= count

    if source_row <= playing_row < source_row + count:
        return insert_row + (playing_row - source_row)
    if source_row < playing_row and destination_child > playing_row:
        return playing_row - count
    if source_row > playing_row and destination_child <= playing_row:
        return playing_row + count
    return playing_row


def next_autoplay_row(playing_row, row_count):
    """Wiersz, na który autoplay przechodzi po bieżącym; -1 gdy nie ma dokąd.

    Zawija z ostatniej pozycji na pierwszą. Playlista z jedną pozycją
    zatrzymuje się na tej pozycji, a wiersz spoza playlisty nie daje celu.
    """
    if row_count <= 1 or not 0 <= playing_row < row_count:
        return -1
    return (playing_row + 1) % row_count


def previous_autoplay_row(playing_row, row_count):
    """Wiersz cofnięty o jeden w trybie autoplay; -1 gdy nie ma dokąd.

    Nie zawija z pierwszej pozycji na ostatnią. Playlista z jedną pozycją
    zatrzymuje się na tej pozycji, a wiersz spoza playlisty nie daje celu.
    """
    if row_count <= 1 or not 0 < playing_row < row_count:
        return -1
    return playing_row - 1


@dataclass
class PlaylistEntry:
    path: str
    filename: str
    overlay: bool = False
    overlay_path: str | None = None


class PlaylistStore:
    """Właściciel wierszy playlisty. Nie zna stanu odtwarzania."""

    def __init__(self):
        self._entries: list[PlaylistEntry] = []

    def rows(self):
        return tuple(self._entries)

    def row_count(self):
        return len(self._entries)

    def entry_at(self, row):
        return self._entries[row]

    def path_at(self, row):
        return self._entries[row].path

    @staticmethod
    def _entry_for(path):
        return PlaylistEntry(path=path, filename=os.path.basename(path))

    def insert_blanks(self, row, count):
        entries = [self._entry_for("") for _ in range(count)]
        self._entries[row:row] = entries

    def add(self, paths, row=None):
        insert_row = self.row_count() if row is None or row == -1 else row
        entries = [self._entry_for(path) for path in paths]
        self._entries[insert_row:insert_row] = entries
        return insert_row

    def remove(self, row, count):
        del self._entries[row : row + count]

    def clear(self):
        self._entries = []

    def can_move(self, source_row, count, destination_child):
        return not (source_row == destination_child or source_row == destination_child - 1)

    def move(self, source_row, count, destination_child):
        items = self._entries[source_row : source_row + count]
        del self._entries[source_row : source_row + count]

        insert_row = destination_child
        if source_row < destination_child:
            insert_row -= count

        self._entries[insert_row:insert_row] = items
        return insert_row

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
            entry = self._entries[row]
            entry.overlay = bool(enabled and entry.overlay_path)

    def set_overlay_path(self, row, path):
        if 0 <= row < len(self._entries):
            self._entries[row].overlay_path = path
            if not path:
                self._entries[row].overlay = False

    def set_overlay_state(self, row, overlay, overlay_path):
        if 0 <= row < len(self._entries):
            entry = self._entries[row]
            entry.overlay = bool(overlay and overlay_path)
            entry.overlay_path = overlay_path
