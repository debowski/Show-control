"""Jedno źródło definicji skrótów klawiszowych.

Każda akcja niesie klawisze oraz klucz etykiety w ``ui/i18n.py``. Dzięki temu
tabela jest jedynym miejscem, w którym opisuje się skrót i jego podpis;
``apply_translations`` nie powiela tych samych tekstów.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence

from showcontrol.ui.i18n import DEFAULT_LANGUAGE, get_t

KEYBOARD_SHORTCUTS = {
    "search": {"keys": [Qt.Key.Key_F3], "label": "search_placeholder"},
    "focus_playlist": {"keys": [Qt.Key.Key_F2]},
    "play": {
        "keys": [Qt.Key.Key_F4],
        "playlist_keys": [Qt.Key.Key_Return, Qt.Key.Key_Enter],
        "label": "play_short",
        "tooltip": "play_short",
    },
    "pause": {
        "keys": [Qt.Key.Key_Space],
        "label": "pause_short",
        "tooltip": "pause_short",
    },
    "stop": {
        "keys": [Qt.Key.Key_F5],
        "label": "stop_short",
        "tooltip": "stop_short",
    },
    "remove": {
        "keys": [Qt.Key.Key_Delete],
        "label": "remove_short",
        "tooltip": "remove_short",
    },
    "save_project": {
        "keys": [Qt.Key.Key_F12],
        "label": "save_project",
        "tooltip": "save_project_tooltip",
    },
    "fade_out": {
        "keys": [Qt.Key.Key_F1],
        "label": "fade_out",
        "tooltip": "fade_out",
    },
    "fullscreen": {
        "keys": [Qt.Key.Key_F11],
        "label": "fullscreen",
        "tooltip": "fullscreen",
    },
    "overlay_on_audio": {
        "keys": [Qt.Key.Key_F10],
        "label": "overlay_on_audio",
    },
    "force_overlay": {
        "keys": [Qt.Key.Key_F9],
        "label": "force_overlay",
    },
    "previous": {
        "keys": [Qt.Key.Key_F6],
        "navigation": {
            "remote": Qt.Key.Key_Left,
            "standard": Qt.Key.Key_Up,
        },
        "label": "previous_short",
        "tooltip": "previous_short",
    },
    "next": {
        "keys": [Qt.Key.Key_F7],
        "navigation": {
            "remote": Qt.Key.Key_Right,
            "standard": Qt.Key.Key_Down,
        },
        "label": "next_short",
        "tooltip": "next_short",
    },
}

# Klawisz -> (krótka etykieta, etykieta do tooltipa), obie jako klucze i18n.
KEY_LABEL_KEYS = {
    Qt.Key.Key_Delete: ("key_delete_short", "key_delete_long"),
    Qt.Key.Key_Down: ("key_down_short", "key_down_long"),
    Qt.Key.Key_Enter: ("key_enter_short", "key_enter_long"),
    Qt.Key.Key_Left: ("key_left_short", "key_left_long"),
    Qt.Key.Key_Return: ("key_enter_short", "key_enter_long"),
    Qt.Key.Key_Right: ("key_right_short", "key_right_long"),
    Qt.Key.Key_Space: ("key_space_short", "key_space_long"),
    Qt.Key.Key_Up: ("key_up_short", "key_up_long"),
}


def key_label(key, language=DEFAULT_LANGUAGE, tooltip=False):
    label_keys = KEY_LABEL_KEYS.get(key)
    if label_keys is None:
        return QKeySequence(key).toString(QKeySequence.SequenceFormat.NativeText)
    short_key, long_key = label_keys
    return get_t(language, long_key if tooltip else short_key)


def shortcut_label(name, language=DEFAULT_LANGUAGE, groups=("keys",), extra_keys=None, separator="/", tooltip=False):
    keys = []
    for group in groups:
        keys.extend(KEYBOARD_SHORTCUTS[name].get(group, []))
    if extra_keys:
        keys.extend(extra_keys)

    labels = []
    for key in keys:
        label = key_label(key, language, tooltip)
        if label and label not in labels:
            labels.append(label)
    return separator.join(labels)


def shortcut_description(name, language=DEFAULT_LANGUAGE, tooltip=False, **kwargs):
    """Zwraca ``etykieta (klawisze)``; akcje bez podpisu dają ``None``."""
    spec = KEYBOARD_SHORTCUTS[name]
    label_key = spec.get("tooltip" if tooltip else "label")
    if not label_key:
        return None
    keys = shortcut_label(name, language=language, tooltip=tooltip, **kwargs)
    return f"{get_t(language, label_key)} ({keys})"


def navigation_shortcut(name, remote_enabled):
    mode = "remote" if remote_enabled else "standard"
    return KEYBOARD_SHORTCUTS[name]["navigation"][mode]
