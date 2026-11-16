"""Jedno źródło definicji skrótów klawiszowych."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence

KEYBOARD_SHORTCUTS = {
    "search": {"keys": [Qt.Key.Key_F3]},
    "focus_playlist": {"keys": [Qt.Key.Key_F2]},
    "play": {
        "keys": [Qt.Key.Key_F4],
        "playlist_keys": [Qt.Key.Key_Return, Qt.Key.Key_Enter],
    },
    "pause": {"keys": [Qt.Key.Key_Space]},
    "stop": {"keys": [Qt.Key.Key_F5]},
    "remove": {"keys": [Qt.Key.Key_Delete]},
    "save_project": {"keys": [Qt.Key.Key_F12]},
    "fade_out": {"keys": [Qt.Key.Key_F1]},
    "fullscreen": {"keys": [Qt.Key.Key_F11]},
    "overlay_on_audio": {"keys": [Qt.Key.Key_F10]},
    "force_overlay": {"keys": [Qt.Key.Key_F9]},
    "previous": {
        "keys": [Qt.Key.Key_F6],
        "navigation": {
            "remote": Qt.Key.Key_Left,
            "standard": Qt.Key.Key_Up,
        },
    },
    "next": {
        "keys": [Qt.Key.Key_F7],
        "navigation": {
            "remote": Qt.Key.Key_Right,
            "standard": Qt.Key.Key_Down,
        },
    },
}

KEY_LABELS = {
    Qt.Key.Key_Delete: "Del",
    Qt.Key.Key_Down: "↓",
    Qt.Key.Key_Enter: "Enter",
    Qt.Key.Key_Left: "←",
    Qt.Key.Key_Return: "Enter",
    Qt.Key.Key_Right: "→",
    Qt.Key.Key_Space: "Spacja",
    Qt.Key.Key_Up: "↑",
}

KEY_TOOLTIP_LABELS = {
    Qt.Key.Key_Delete: "Delete",
    Qt.Key.Key_Down: "Strzałka w dół",
    Qt.Key.Key_Left: "Strzałka w lewo",
    Qt.Key.Key_Right: "Strzałka w prawo",
    Qt.Key.Key_Up: "Strzałka w górę",
}


def key_label(key, tooltip=False):
    labels = KEY_TOOLTIP_LABELS if tooltip else KEY_LABELS
    return labels.get(key, QKeySequence(key).toString(QKeySequence.SequenceFormat.NativeText))


def shortcut_label(name, groups=("keys",), extra_keys=None, separator="/", tooltip=False):
    keys = []
    for group in groups:
        keys.extend(KEYBOARD_SHORTCUTS[name].get(group, []))
    if extra_keys:
        keys.extend(extra_keys)

    labels = []
    for key in keys:
        label = key_label(key, tooltip)
        if label and label not in labels:
            labels.append(label)
    return separator.join(labels)


def navigation_shortcut(name, remote_enabled):
    mode = "remote" if remote_enabled else "standard"
    return KEYBOARD_SHORTCUTS[name]["navigation"][mode]
