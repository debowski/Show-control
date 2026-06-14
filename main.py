# Show-control Version 0.3.4
# Copyright (C) 2026 Piotr Dębowski
#
# Professional Broadcast Edition

import sys
import os
import time
import json
import logging

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QSlider, QListView,
                             QFileDialog, QMessageBox, QCheckBox, QStackedLayout,
                             QLabel, QGroupBox, QAbstractItemView, QSizePolicy,
                             QLineEdit, QSpinBox, QComboBox)
from PyQt6.QtCore import Qt, QTimer, QAbstractListModel, QModelIndex, QUrl, QSortFilterProxyModel, QSettings
from PyQt6.QtGui import QShortcut, QKeySequence, QPainter, QColor, QPixmap, QFont, QIcon

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    import vlc
except ImportError:
    print("Błąd: Biblioteka python-vlc nie jest zainstalowana.")
    print("Zainstaluj ją używając: pip install python-vlc")
    sys.exit(1)

MEDIA_EXTENSIONS = ('.mp4', '.mp3', '.mkv', '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.wav', '.flac', '.aac', '.ogg', '.m4a')
AUDIO_EXTENSIONS = ('.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a')
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
PROJECT_FILE_FILTER = "JSON (*.json)"
MEDIA_FILE_FILTER = "Media (*.mp4 *.mp3 *.mkv *.jpg *.png);;Wszystkie (*.*)"
EMPTY_TIME_LABEL = "00:00 / 00:00 (Pozostało: -00:00)"

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
    "logo_audio": {"keys": [Qt.Key.Key_F10]},
    "logo_overlay": {"keys": [Qt.Key.Key_F9]},
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


def has_extension(path, extensions):
    return bool(path and path.lower().endswith(extensions))


def is_audio_file(path):
    return has_extension(path, AUDIO_EXTENSIONS)


def is_image_file(path):
    return has_extension(path, IMAGE_EXTENSIONS)


def is_supported_media_file(path):
    return has_extension(path, MEDIA_EXTENSIONS)


def find_media_paths(path):
    if os.path.isfile(path):
        return [path] if is_supported_media_file(path) else []

    if not os.path.isdir(path):
        return []

    paths = []
    for root, _, files in os.walk(path):
        for filename in files:
            media_path = os.path.join(root, filename)
            if is_supported_media_file(media_path):
                paths.append(media_path)
    return paths

# ---------------------------------------------------------------------------
# THEME ENGINE
# ---------------------------------------------------------------------------

# Each theme is a flat dict of color tokens consumed by generate_stylesheet().
THEMES = {
    "dark": {
        "name": "Studio Dark",
        "bg_main":   "#1e1e1e",
        "bg_dark":   "#252526",
        "bg_btn":    "#333333",
        "bg_hover":  "#3e3e42",
        "accent":    "#007acc",
        "accent_hi": "#005a9e",
        "flash_glow":"#6bbcff",
        "play":      "#2d8a49",
        "play_hi":   "#3aa659",
        "stop":      "#a1260d",
        "stop_hi":   "#be2d10",
        "fade":      "#d18616",
        "fade_hi":   "#e5951a",
        "hide":      "#4a4a4a",
        "text":      "#d4d4d4",
        "text_dim":  "#aaaaaa",
        "border":    "#3c3c3c",
        "list_play": "#094771",
    },
    "light": {
        "name": "Studio Light",
        "bg_main":   "#f0f0f0",
        "bg_dark":   "#e4e4e4",
        "bg_btn":    "#dcdcdc",
        "bg_hover":  "#c8c8c8",
        "accent":    "#0063b1",
        "accent_hi": "#004e8a",
        "flash_glow":"#0078d7",
        "play":      "#107c10",
        "play_hi":   "#0e6b0e",
        "stop":      "#c42b1c",
        "stop_hi":   "#a52315",
        "fade":      "#ca5010",
        "fade_hi":   "#b8460e",
        "hide":      "#8a8a8a",
        "text":      "#1a1a1a",
        "text_dim":  "#555555",
        "border":    "#b0b0b0",
        "list_play": "#cce4f7",
    },
    "stealth": {
        "name": "Red Night (Stealth)",
        "bg_main":   "#0a0000",
        "bg_dark":   "#120000",
        "bg_btn":    "#200000",
        "bg_hover":  "#2e0000",
        "accent":    "#cc0000",
        "accent_hi": "#990000",
        "flash_glow":"#ff4444",
        "play":      "#8b0000",
        "play_hi":   "#a00000",
        "stop":      "#4a0000",
        "stop_hi":   "#5e0000",
        "fade":      "#7a3000",
        "fade_hi":   "#8e3800",
        "hide":      "#1e0000",
        "text":      "#cc4444",
        "text_dim":  "#883333",
        "border":    "#3a0000",
        "list_play": "#330000",
    },
    "broadcast": {
        "name": "Broadcast Indigo",
        "bg_main":   "#12131f",
        "bg_dark":   "#1a1b2e",
        "bg_btn":    "#252640",
        "bg_hover":  "#32335a",
        "accent":    "#6c63ff",
        "accent_hi": "#4b44cc",
        "flash_glow":"#a89cff",
        "play":      "#2ecc71",
        "play_hi":   "#27ae60",
        "stop":      "#e74c3c",
        "stop_hi":   "#c0392b",
        "fade":      "#f39c12",
        "fade_hi":   "#d68910",
        "hide":      "#3d3d5c",
        "text":      "#e8e8ff",
        "text_dim":  "#9999cc",
        "border":    "#3a3a5c",
        "list_play": "#1e1f40",
    },
}

THEME_KEYS = list(THEMES.keys())
DEFAULT_THEME = "dark"


def generate_stylesheet(theme_key: str) -> str:
    """Build and return a full QSS stylesheet for the given theme key."""
    t = THEMES.get(theme_key, THEMES[DEFAULT_THEME])
    return f"""
    QMainWindow, QWidget {{
        background-color: {t['bg_main']};
        color: {t['text']};
        font-family: 'Segoe UI', system-ui;
        font-size: 10pt;
    }}

    QGroupBox {{
        border: 1px solid {t['border']};
        border-radius: 4px;
        margin-top: 1.2em;
        font-weight: bold;
        color: {t['accent']};
        padding: 10px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
    }}

    /* --- Buttons base --- */
    QPushButton {{
        background-color: {t['bg_btn']};
        color: {t['text']};
        border: 1px solid {t['border']};
        padding: 8px 15px;
        border-radius: 3px;
        min-height: 22px;
    }}
    QPushButton:hover  {{ background-color: {t['bg_hover']}; }}
    QPushButton:pressed {{ background-color: {t['accent']}; color: white; }}
    QPushButton:checked {{
        background-color: {t['accent']};
        color: white;
        font-weight: bold;
        border: 1px solid {t['accent_hi']};
    }}

    /* --- Transport buttons --- */
    QPushButton#PlayBtn {{
        background-color: {t['play']};
        color: white;
        font-weight: bold;
        font-size: 11pt;
        min-height: 45px;
    }}
    QPushButton#PlayBtn:hover  {{ background-color: {t['play_hi']}; }}

    QPushButton#StopBtn {{
        background-color: {t['stop']};
        color: white;
        font-weight: bold;
        font-size: 11pt;
        min-height: 45px;
    }}
    QPushButton#StopBtn:hover  {{ background-color: {t['stop_hi']}; }}

    QPushButton#TransportBtn {{
        font-weight: bold;
        min-height: 45px;
    }}

    QPushButton#FadeBtn {{
        background-color: {t['fade']};
        color: white;
    }}
    QPushButton#FadeBtn:hover  {{ background-color: {t['fade_hi']}; }}

    QPushButton#HideBtn {{
        background-color: {t['hide']};
        color: {t['text_dim']};
    }}

    /* --- Flash state (all named variants) --- */
    QPushButton[flash="true"] {{
        background-color: {t['accent']};
        color: white;
        border: 2px solid {t['flash_glow']};
        font-weight: bold;
    }}

    /* --- Lists --- */
    QListView {{
        background-color: {t['bg_dark']};
        border: 1px solid {t['border']};
        outline: none;
        alternate-background-color: {t['bg_main']};
    }}
    QListView::item:hover {{
        background-color: {t['bg_hover']};
    }}
    QListView::item:selected {{
        background-color: {t['accent']};
        color: white;
    }}

    /* --- Inputs --- */
    QLineEdit, QSpinBox, QComboBox {{
        background-color: {t['bg_dark']};
        border: 1px solid {t['border']};
        color: {t['text']};
        padding: 4px 6px;
        border-radius: 3px;
        min-height: 22px;
    }}

    /* SpinBox — jawnie definiujemy przyciski, bo QSS wyłącza domyślny natywny wygląd */
    QSpinBox {{
        padding-right: 20px;  /* zostaw miejsce na przyciski */
    }}
    QSpinBox::up-button {{
        subcontrol-origin: border;
        subcontrol-position: top right;
        width: 18px;
        border-left: 1px solid {t['border']};
        border-bottom: 1px solid {t['border']};
        border-top-right-radius: 3px;
        background-color: {t['bg_btn']};
    }}
    QSpinBox::down-button {{
        subcontrol-origin: border;
        subcontrol-position: bottom right;
        width: 18px;
        border-left: 1px solid {t['border']};
        border-bottom-right-radius: 3px;
        background-color: {t['bg_btn']};
    }}
    QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
        background-color: {t['bg_hover']};
    }}
    QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {{
        background-color: {t['accent']};
    }}
    QSpinBox::up-arrow {{
        width: 7px; height: 7px;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-bottom: 5px solid {t['text_dim']};
    }}
    QSpinBox::down-arrow {{
        width: 7px; height: 7px;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid {t['text_dim']};
    }}
    QSpinBox::up-arrow:hover, QSpinBox::down-arrow:hover {{
        border-bottom-color: {t['accent']};
        border-top-color: {t['accent']};
    }}

    QComboBox::drop-down {{ border: none; }}
    QComboBox QAbstractItemView {{
        background-color: {t['bg_dark']};
        color: {t['text']};
        selection-background-color: {t['accent']};
    }}

    /* --- Sliders --- */
    QSlider::groove:horizontal {{
        border: 1px solid {t['border']};
        height: 8px;
        background: {t['bg_dark']};
        border-radius: 4px;
    }}
    QSlider::handle:horizontal {{
        background: {t['accent']};
        width: 18px;
        height: 18px;
        margin: -6px 0;
        border-radius: 9px;
    }}
    QSlider::groove:vertical {{
        border: 1px solid {t['border']};
        width: 8px;
        background: {t['bg_dark']};
        border-radius: 4px;
    }}
    QSlider::handle:vertical {{
        background: {t['accent']};
        width: 18px;
        height: 18px;
        margin: 0 -6px;
        border-radius: 9px;
    }}

    /* --- Scrollbars --- */
    QScrollBar:vertical {{
        background: {t['bg_dark']};
        width: 10px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical {{
        background: {t['border']};
        border-radius: 5px;
        min-height: 20px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

    /* --- Time label --- */
    QLabel#TimeLabel {{
        font-size: 13pt;
        font-weight: bold;
        color: {t['text']};
    }}

    /* --- Move buttons (lista) --- */
    QPushButton#MoveBtn {{
        background-color: transparent;
        color: {t['text_dim']};
        border: 1px solid transparent;
        border-radius: 4px;
        font-size: 9pt;
        padding: 0px;
    }}
    QPushButton#MoveBtn:hover {{
        background-color: {t['bg_hover']};
        color: {t['accent']};
        border: 1px solid {t['border']};
    }}
    QPushButton#MoveBtn:pressed {{
        background-color: {t['accent']};
        color: white;
    }}
    """


class LogoViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logo_pixmap = None
        self.show_logo = True
        self.opacity = 1.0
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        if self.show_logo and self.logo_pixmap and not self.logo_pixmap.isNull():
            scaled = self.logo_pixmap.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            painter.setOpacity(self.opacity)
            painter.drawPixmap(int((w - scaled.width())/2), int((h - scaled.height())/2), scaled)

class ProjectionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.Window)
        self.setWindowTitle("Projekcja - Odtwarzacz")
        self.setStyleSheet("background-color: black;")
        self.video_widget = QWidget()
        self.logo_container = QWidget()
        self.logo_stacked_layout = QStackedLayout(self.logo_container)
        self.logo_stacked_layout.setContentsMargins(0, 0, 0, 0)
        self.logo_viewer = LogoViewer()
        self.logo_video_widget = QWidget()
        self.logo_stacked_layout.addWidget(self.logo_viewer)
        self.logo_stacked_layout.addWidget(self.logo_video_widget)
        self.stacked_layout = QStackedLayout(self)
        self.stacked_layout.addWidget(self.video_widget)
        self.stacked_layout.addWidget(self.logo_container)
        self.set_mode_video()

                # --- DODAWANIE IKONY ---
        # Ścieżka do pliku .ico w tym samym folderze
        nazwa_pliku_ikony = 'ikona_bw.ico'
        sciezka_do_ikony = os.path.join(os.path.dirname(__file__), nazwa_pliku_ikony)

        # Sprawdź na wszelki wypadek, czy plik istnieje
        if os.path.exists(sciezka_do_ikony):
            self.setWindowIcon(QIcon(sciezka_do_ikony))
        else:
            print(f"Ostrzeżenie: Nie znaleziono pliku ikony pod adresem: {sciezka_do_ikony}")

    def set_mode_video(self):
        self.stacked_layout.setCurrentWidget(self.video_widget)
        
    def set_mode_audio(self):
        self.stacked_layout.setCurrentWidget(self.logo_container)
        
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()

    def move_to_second_screen(self):
        screens = QApplication.screens()
        if len(screens) > 1:
            second_screen = screens[1]
            self.resize(800, 600)
            self.move(second_screen.geometry().topLeft() + second_screen.geometry().center() - self.rect().center())
            self.showFullScreen()
        else:
            self.resize(800, 600)

    def closeEvent(self, event):
        # Zamiast całkowicie kasować okno podglądu przy "X", po prostu je chowamy.
        # Zapobiega to utracie HWND.
        event.ignore()
        self.hide()

class PlaylistModel(QAbstractListModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []  # Lista słowników: [{'filename': '...', 'path': '...'}]
        self.playing_row = -1

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
            
        row = index.row()
        item = self._data[row]
        
        if role == Qt.ItemDataRole.DisplayRole:
            return item['filename']
        elif role == Qt.ItemDataRole.UserRole:
            return item['path']
        elif role == Qt.ItemDataRole.ToolTipRole:
            return item['path'] + (" [nakładka]" if item.get('overlay', False) else "")
        elif role == Qt.ItemDataRole.CheckStateRole:
            return Qt.CheckState.Checked if item.get('overlay', False) else Qt.CheckState.Unchecked
        elif role == Qt.ItemDataRole.BackgroundRole:
            if row == self.playing_row:
                return QColor("#094771")
        elif role == Qt.ItemDataRole.FontRole:
            if row == self.playing_row:
                return QFont("Segoe UI", 10, QFont.Weight.Bold)
                
        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid():
            return False
        if role == Qt.ItemDataRole.CheckStateRole:
            checked = (value == Qt.CheckState.Checked) if isinstance(value, Qt.CheckState) else bool(value)
            self._data[index.row()]['overlay'] = checked
            self.dataChanged.emit(index, index, [role])
            return True
        return False

    def flags(self, index):
        default_flags = super().flags(index)
        if index.isValid():
            return default_flags | Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable
        return default_flags | Qt.ItemFlag.ItemIsDropEnabled

    def supportedDropActions(self):
        return Qt.DropAction.CopyAction | Qt.DropAction.MoveAction

    def mimeTypes(self):
        return ["text/uri-list", "application/x-qabstractitemmodeldatalist"]

    def mimeData(self, indexes):
        mime_data = super().mimeData(indexes)
        urls = []
        for index in indexes:
            if index.isValid():
                path = self._data[index.row()]['path']
                urls.append(QUrl.fromLocalFile(path))
        mime_data.setUrls(urls)
        return mime_data

    def dropMimeData(self, data, action, row, _column, parent):
        if action == Qt.DropAction.IgnoreAction:
            return True

        target_row = row if row != -1 else self.rowCount()

        if data.hasFormat("application/x-qabstractitemmodeldatalist") and data.hasUrls():
            return self._move_dropped_rows(data.urls(), target_row)

        if data.hasUrls():
            paths = []
            for url in data.urls():
                paths.extend(find_media_paths(url.toLocalFile()))
            return self.add_files(paths, target_row, parent)

        return False

    def _move_dropped_rows(self, urls, target_row):
        for url in urls:
            source_row = self.row_for_path(url.toLocalFile())
            if source_row == -1:
                continue

            self.moveRows(QModelIndex(), source_row, 1, QModelIndex(), target_row)
            if source_row < target_row:
                target_row -= 1
        return True

    def row_for_path(self, path):
        for idx, item in enumerate(self._data):
            if item['path'] == path:
                return idx
        return -1

    def insertRows(self, row, count, parent=QModelIndex()):
        self.beginInsertRows(parent, row, row + count - 1)
        for _ in range(count):
            self._data.insert(row, {'filename': '', 'path': '', 'overlay': False})
        # Aktualizacja indeksu odtwarzania przy wstawianiu powyżej
        if self.playing_row >= row:
            self.playing_row += count
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent=QModelIndex()):
        self.beginRemoveRows(parent, row, row + count - 1)
        del self._data[row:row+count]
        # Aktualizacja indeksu odtwarzania przy usuwaniu
        if self.playing_row >= row and self.playing_row < row + count:
            self.playing_row = -1
        elif self.playing_row >= row + count:
            self.playing_row -= count
        self.endRemoveRows()
        return True

    def _update_playing_row_on_move(self, sourceRow, count, destinationChild, insert_row):
        if sourceRow <= self.playing_row < sourceRow + count:
            offset = self.playing_row - sourceRow
            self.playing_row = insert_row + offset
        else:
            # Jeśli element przesuwa się przez playing_row
            if sourceRow < self.playing_row and destinationChild > self.playing_row:
                self.playing_row -= count
            elif sourceRow > self.playing_row and destinationChild <= self.playing_row:
                self.playing_row += count

    def moveRows(self, sourceParent, sourceRow, count, destinationParent, destinationChild):
        # Sprawdzamy czy nie przenosimy w to samo miejsce
        if sourceRow == destinationChild or sourceRow == destinationChild - 1:
            return False
            
        self.beginMoveRows(sourceParent, sourceRow, sourceRow + count - 1, destinationParent, destinationChild)
        items_to_move = self._data[sourceRow:sourceRow+count]
        
        del self._data[sourceRow:sourceRow+count]
        
        insert_row = destinationChild
        if sourceRow < destinationChild:
            insert_row -= count
            
        for i, item in enumerate(items_to_move):
            self._data.insert(insert_row + i, item)
            
        self._update_playing_row_on_move(sourceRow, count, destinationChild, insert_row)
                
        self.endMoveRows()
        return True


    def add_files(self, file_paths, row=None, parent=QModelIndex()):
        file_paths = [path for path in file_paths if path]
        if not file_paths:
            return False

        insert_row = self.rowCount() if row is None or row == -1 else row
        self.insertRows(insert_row, len(file_paths), parent)

        for offset, path in enumerate(file_paths):
            self._data[insert_row + offset] = {
                'filename': os.path.basename(path),
                'path': path,
                'overlay': False
            }

        self.dataChanged.emit(self.index(insert_row, 0), self.index(insert_row + len(file_paths) - 1, 0))
        return True

    def clear(self):
        self.beginResetModel()
        self._data = []
        self.playing_row = -1
        self.endResetModel()

    def file_paths(self):
        return [item['path'] for item in self._data]

    def overlay_for_row(self, row):
        """Zwraca True jeśli dany wiersz ma ustawioną nakładkę."""
        if 0 <= row < len(self._data):
            return self._data[row].get('overlay', False)
        return False

    def set_playing_row(self, row):
        old_row = self.playing_row
        self.playing_row = row
        
        if old_row != -1:
            self.dataChanged.emit(self.index(old_row, 0), self.index(old_row, 0))
        if row != -1:
            self.dataChanged.emit(self.index(row, 0), self.index(row, 0))

class PlaylistView(QListView):
    """QListView z prawidłową obsługą wewnętrznego przenoszenia oraz drag & drop z zewnątrz."""

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        # Jeśli przeciągamy element wewnątrz tego samego widoku
        if event.source() == self:
            # Pozwalamy Qt na standardowe obsłużenie MoveAction przez model/proxy
            super().dropEvent(event)
        elif event.mimeData().hasUrls():
            # Elementy z zewnątrz (np. z Eksploratora) wymuszają CopyAction
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            model = self.model()
            if model:
                pos = event.position().toPoint()
                idx = self.indexAt(pos)
                row = idx.row() if idx.isValid() else -1
                model.dropMimeData(event.mimeData(), Qt.DropAction.CopyAction, row, 0, idx.parent())
        else:
            super().dropEvent(event)


class PlaylistFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        
    def filterAcceptsRow(self, source_row, source_parent):
        # Akceptuj wszystko jeśli filtr pusty
        if not self.filterRegularExpression().pattern():
            return True
            
        model = self.sourceModel()
        index = model.index(source_row, 0, source_parent)
        filename = model.data(index, Qt.ItemDataRole.DisplayRole)
        
        if filename:
            # match instead of indexof
            return self.filterRegularExpression().match(filename).hasMatch()
        return False

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("ShowControl", "OperatorConsole")
        self.base_title = "Show Control - Operator Console v0.3.4"
        self.setWindowTitle(self.base_title)
        self.setMinimumSize(900, 700)
        
        # --- DODAWANIE IKONY ---
        # Ścieżka do pliku .ico w tym samym folderze
        nazwa_pliku_ikony = 'ikona_sc.ico'
        sciezka_do_ikony = os.path.join(os.path.dirname(__file__), nazwa_pliku_ikony)

        # Sprawdź na wszelki wypadek, czy plik istnieje
        if os.path.exists(sciezka_do_ikony):
            self.setWindowIcon(QIcon(sciezka_do_ikony))
        else:
            print(f"Ostrzeżenie: Nie znaleziono pliku ikony pod adresem: {sciezka_do_ikony}")


        try:
            self.vlc_instance = vlc.Instance('--no-xlib', '--quiet', '--aout=waveout', '--video-filter=adjust')
            self.media_player = self.vlc_instance.media_player_new()
            self.media_player.audio_set_volume(0) # Konfiguracja zabezpieczająca na start
            self.media_player.video_set_adjust_int(vlc.VideoAdjustOption.Enable, 1)
            self.logo_player = self.vlc_instance.media_player_new()
            self.logo_player.audio_set_volume(0)
            self.logo_player.video_set_adjust_int(vlc.VideoAdjustOption.Enable, 1)
        except Exception as e:
            QMessageBox.critical(self, "VLC Error", f"Błąd VLC: {e}")
            sys.exit(1)

        self.projection_window = ProjectionWindow()
        self.projection_window.move_to_second_screen()
        self.projection_window.show()
        
        if sys.platform.startswith("win"):
            self.media_player.set_hwnd(int(self.projection_window.video_widget.winId()))
            self.logo_player.set_hwnd(int(self.projection_window.logo_video_widget.winId()))
        self.media_player.video_set_mouse_input(False)
        self.media_player.video_set_key_input(False)
        self.logo_player.video_set_mouse_input(False)
        self.logo_player.video_set_key_input(False)
        
        self.init_ui()
        self.image_autoplay_timer = QTimer(self)
        self.image_autoplay_timer.setSingleShot(True)
        self.image_autoplay_timer.timeout.connect(self._on_image_autoplay_timeout)
        self.fade_timer = QTimer(self)
        self.fade_timer.timeout.connect(self._fade_out_step)
        self._fade_state = None
        self.image_autoplay_start = None
        self.image_autoplay_duration = 0
        self.is_playing = False
        self.is_transitioning = False
        self.user_is_seeking = False
        
        last_project = self.settings.value("last_project", "")
        if last_project and os.path.exists(last_project):
            # Używamy QTimer by załadować projekt po pełnym zainicjalizowaniu UI
            QTimer.singleShot(100, lambda: self._load_project_file(last_project))
            
    def update_window_title(self, path):
        if path:
            name = os.path.basename(path)
            self.setWindowTitle(f"{self.base_title} - [{name}]")
        else:
            self.setWindowTitle(self.base_title)
            
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # --- GÓRNY PASEK ZARZĄDZANIA ---
        top_bar = QHBoxLayout()
        mgmt_left = QHBoxLayout()
        self.add_btn = QPushButton("✚ Dodaj pliki")
        self.add_btn.setToolTip("Dodaj nowe pliki do listy")
        self.add_btn.clicked.connect(self.add_files)
        self.remove_btn = QPushButton()
        self.remove_btn.clicked.connect(self.remove_file)
        mgmt_left.addWidget(self.add_btn)
        mgmt_left.addWidget(self.remove_btn)
        
        mgmt_right = QHBoxLayout()
        self.load_proj_btn = QPushButton("📂 Wczytaj Projekt")
        self.load_proj_btn.setToolTip("Wczytaj zapisaną listę plików")
        self.load_proj_btn.clicked.connect(self.load_project)
        self.save_proj_btn = QPushButton()
        self.save_proj_btn.clicked.connect(self.save_project)
        mgmt_right.addWidget(self.load_proj_btn)
        mgmt_right.addWidget(self.save_proj_btn)
        
        top_bar.addLayout(mgmt_left)
        top_bar.addStretch()
        
        self.logo_btn = QPushButton("📁 Wybierz plik nakładki")
        self.logo_btn.setToolTip("Wybierz obrazek lub grafikę do wyświetlania")
        self.logo_btn.clicked.connect(self.select_logo)
        
        self.window_btn = QPushButton("👁 Ukryj Okno")
        self.window_btn.setObjectName("HideBtn")
        self.window_btn.setToolTip("Ukryj lub pokaż okno projekcji")
        self.window_btn.clicked.connect(self.toggle_projection_window)
        
        mgmt_center = QHBoxLayout()
        mgmt_center.addWidget(self.logo_btn)
        mgmt_center.addWidget(self.window_btn)
        top_bar.addLayout(mgmt_center)
        
        top_bar.addStretch()
        top_bar.addLayout(mgmt_right)
        layout.addLayout(top_bar)

        # --- PASEK WYSZUKIWANIA ---
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.filter_playlist)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # --- LISTA PLIKÓW ---
        self.playlist_model = PlaylistModel(self)
        self.proxy_model = PlaylistFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.playlist_model)
        # Na żywo aktualizuj tryb projekcji gdy operator zmieni checkbox nakładki
        self.playlist_model.dataChanged.connect(self._on_playlist_overlay_changed)
        
        self.playlist = PlaylistView(self)
        self.playlist.setModel(self.proxy_model)
        self.playlist.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.playlist.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.playlist.setAlternatingRowColors(True)
        
        # Konfiguracja Drag & Drop
        # DragDrop (nie InternalMove) pozwala akceptować pliki z zewnątrz (Eksplorator)
        self.playlist.setDragEnabled(True)
        self.playlist.setAcceptDrops(True)
        self.playlist.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.playlist.setDropIndicatorShown(True)
        self.playlist.setDefaultDropAction(Qt.DropAction.MoveAction)
        
        self.playlist.doubleClicked.connect(lambda idx: self.play_media())

        # --- PRZYCISKI PRZESUWANIA KOLEJNOŚCI ---
        self.move_up_btn = QPushButton("▲")
        self.move_up_btn.setObjectName("MoveBtn")
        self.move_up_btn.setToolTip("Przesuń plik w górę")
        self.move_up_btn.setFixedSize(28, 28)
        self.move_up_btn.clicked.connect(self.move_item_up)

        self.move_down_btn = QPushButton("▼")
        self.move_down_btn.setObjectName("MoveBtn")
        self.move_down_btn.setToolTip("Przesuń plik w dół")
        self.move_down_btn.setFixedSize(28, 28)
        self.move_down_btn.clicked.connect(self.move_item_down)

        move_btn_layout = QVBoxLayout()
        move_btn_layout.setContentsMargins(0, 0, 0, 0)
        move_btn_layout.setSpacing(4)
        move_btn_layout.addWidget(self.move_up_btn)
        move_btn_layout.addWidget(self.move_down_btn)
        move_btn_layout.addStretch()

        playlist_row = QHBoxLayout()
        playlist_row.setSpacing(6)
        playlist_row.addWidget(self.playlist, stretch=1)
        playlist_row.addLayout(move_btn_layout)
        layout.addLayout(playlist_row, stretch=1)

        # --- SEKCJA TRANSPORTU ---
        transport_frame = QGroupBox("Kontrola odtwarzania")
        trans_layout = QVBoxLayout(transport_frame)
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.setFixedHeight(25)
        self.progress_slider.sliderMoved.connect(self.set_position)
        self.progress_slider.sliderPressed.connect(lambda: setattr(self, 'user_is_seeking', True))
        self.progress_slider.sliderReleased.connect(self.slider_released)
        
        self.time_label = QLabel(EMPTY_TIME_LABEL)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setObjectName("TimeLabel")

        trans_layout.addWidget(self.progress_slider)
        trans_layout.addWidget(self.time_label)
        
        btns_grid = QHBoxLayout()
        btns_grid.setSpacing(5)
        self.prev_btn = QPushButton()
        self.prev_btn.setObjectName("TransportBtn")
        self.prev_btn.clicked.connect(self.play_previous_file)
        
        self.play_btn = QPushButton()
        self.play_btn.setObjectName("PlayBtn")
        self.play_btn.clicked.connect(self.play_media)
        
        self.pause_btn = QPushButton()
        self.pause_btn.setObjectName("TransportBtn")
        self.pause_btn.clicked.connect(self.toggle_play_pause)
        
        self.stop_btn = QPushButton()
        self.stop_btn.setObjectName("StopBtn")
        self.stop_btn.clicked.connect(self.stop_media)
        
        self.next_btn = QPushButton()
        self.next_btn.setObjectName("TransportBtn")
        self.next_btn.clicked.connect(self.play_next_file)
        
        for btn in [self.prev_btn, self.play_btn, self.pause_btn, self.stop_btn, self.next_btn]:
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            btns_grid.addWidget(btn)
        trans_layout.addLayout(btns_grid)
        layout.addWidget(transport_frame)

        # --- DOLNY PANEL ---
        bottom_panel = QHBoxLayout()
        view_group = QGroupBox("Widok i Efekty")
        view_layout = QVBoxLayout(view_group)
        self.fade_btn = QPushButton()
        self.fade_btn.setObjectName("FadeBtn")
        self.fade_btn.clicked.connect(self.fade_out)
        self.fullscreen_btn = QPushButton()
        self.fullscreen_btn.clicked.connect(self.toggle_projection_fullscreen)
        self.logo_overlay_btn = QPushButton()
        self.logo_overlay_btn.setCheckable(True)
        self.logo_overlay_btn.setObjectName("TransportBtn")
        self.logo_overlay_btn.setToolTip("Pokaż obrazek zamiast wideo na wyjściu projekcji")
        self.logo_overlay_btn.toggled.connect(self.toggle_logo_overlay)
        view_layout.addWidget(self.fade_btn)
        view_layout.addWidget(self.fullscreen_btn)
        view_layout.addWidget(self.logo_overlay_btn)
        
        audio_group = QGroupBox("Sterowanie")
        audio_main_layout = QHBoxLayout(audio_group)
        
        # --- Suwak głośności ---
        vol_slider_layout = QVBoxLayout()
        vol_title = QLabel("🔊 Głośność")
        vol_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vol_title.setStyleSheet("font-size: 8pt; color: #aaaaaa;")
        self.vol_label = QLabel("100%")
        self.vol_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.volume_slider = QSlider(Qt.Orientation.Vertical)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        vol_slider_layout.addWidget(vol_title)
        vol_slider_layout.addWidget(self.vol_label)
        vol_slider_layout.addWidget(self.volume_slider, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        # --- Suwak prędkości fade ---
        fade_slider_layout = QVBoxLayout()
        fade_title = QLabel("⏱ Fade")
        fade_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fade_title.setStyleSheet("font-size: 8pt; color: #aaaaaa;")
        self.fade_speed_label = QLabel("2.0s")
        self.fade_speed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fade_speed_slider = QSlider(Qt.Orientation.Vertical)
        # Zakres 2–20 (= 0.2s–2.0s, skalujemy /10 → czyli 10 = 1.0s, 20 = 2.0s)
        self.fade_speed_slider.setRange(2, 20)
        self.fade_speed_slider.setValue(8)   # domyślnie 2.0s
        self.fade_speed_slider.setToolTip("Czas trwania efektu fade (0.2s – 2.0s)")
        self.fade_speed_slider.valueChanged.connect(self._on_fade_speed_changed)
        fade_slider_layout.addWidget(fade_title)
        fade_slider_layout.addWidget(self.fade_speed_label)
        fade_slider_layout.addWidget(self.fade_speed_slider, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        # --- Suwak jasności ---
        bri_slider_layout = QVBoxLayout()
        bri_title = QLabel("💡 Jasność")
        bri_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bri_title.setStyleSheet("font-size: 8pt; color: #aaaaaa;")
        self.bri_label = QLabel("100%")
        self.bri_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.brightness_slider = QSlider(Qt.Orientation.Vertical)
        self.brightness_slider.setRange(0, 100)
        self.brightness_slider.setValue(100)
        self.brightness_slider.setToolTip("Jasność okna projekcji (0% – 100%)")
        self.brightness_slider.valueChanged.connect(self.set_brightness)
        bri_slider_layout.addWidget(bri_title)
        bri_slider_layout.addWidget(self.bri_label)
        bri_slider_layout.addWidget(self.brightness_slider, alignment=Qt.AlignmentFlag.AlignHCenter)

        audio_main_layout.addStretch()
        audio_main_layout.addLayout(vol_slider_layout)
        audio_main_layout.addSpacing(12)
        audio_main_layout.addLayout(bri_slider_layout)
        audio_main_layout.addSpacing(12)
        audio_main_layout.addLayout(fade_slider_layout)
        audio_main_layout.addSpacing(12)

        audio_main_layout.addStretch()
        
        settings_group = QGroupBox("Ustawienia")
        set_layout = QVBoxLayout(settings_group)
        self.autoplay_checkbox = QCheckBox("Autoodtwarzanie")
        self.autoplay_checkbox.stateChanged.connect(self._on_autoplay_changed)

        image_speed_layout = QHBoxLayout()
        image_speed_title = QLabel("⏱ Prędkość grafiki")
        self.image_switch_delay = QSpinBox()
        self.image_switch_delay.setRange(1, 60)
        self.image_switch_delay.setValue(5)
        self.image_switch_delay.setSuffix(" s")
        self.image_switch_delay.setToolTip("Czas wyświetlania plików graficznych w sekundach przy autoodtwarzaniu")
        self.image_switch_delay.setFixedWidth(100)
        image_speed_layout.addWidget(image_speed_title)
        image_speed_layout.addStretch()
        image_speed_layout.addWidget(self.image_switch_delay)

        self.remote_checkbox = QCheckBox("Tryb Pilota (L/P)")
        self.remote_checkbox.setChecked(True)
        self.remote_checkbox.stateChanged.connect(lambda: self.update_shortcuts())
        self.logo_audio_checkbox = QCheckBox()
        self.logo_audio_checkbox.setChecked(True)
        self.logo_audio_checkbox.stateChanged.connect(lambda: self.update_logo_visibility())

        # --- Theme selector ---
        theme_row = QHBoxLayout()
        theme_label = QLabel("🎨 Motyw")
        self.theme_combo = QComboBox()
        for key in THEME_KEYS:
            self.theme_combo.addItem(THEMES[key]["name"], key)
        saved_theme = self.settings.value("theme", DEFAULT_THEME)
        saved_idx = THEME_KEYS.index(saved_theme) if saved_theme in THEME_KEYS else 0
        self.theme_combo.setCurrentIndex(saved_idx)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        theme_row.addWidget(theme_label)
        theme_row.addWidget(self.theme_combo, stretch=1)

        set_layout.addWidget(self.autoplay_checkbox)
        set_layout.addLayout(image_speed_layout)
        set_layout.addWidget(self.remote_checkbox)
        set_layout.addWidget(self.logo_audio_checkbox)
        set_layout.addLayout(theme_row)
        set_layout.addStretch()
        
        bottom_panel.addWidget(view_group, stretch=1)
        bottom_panel.addWidget(audio_group, stretch=1)
        bottom_panel.addWidget(settings_group, stretch=1)
        layout.addLayout(bottom_panel)

        self.setup_button_feedback(
            self.add_btn, self.remove_btn, self.load_proj_btn, self.save_proj_btn,
            self.logo_btn, self.window_btn, self.prev_btn, self.play_btn,
            self.pause_btn, self.stop_btn, self.next_btn, self.fade_btn,
            self.fullscreen_btn, self.logo_overlay_btn,
        )
        self.update_shortcut_descriptions()
        self.init_shortcuts()
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.check_player_status)
        self.status_timer.start(500)

    def init_shortcuts(self):
        for key in KEYBOARD_SHORTCUTS["pause"]["keys"]:
            QShortcut(QKeySequence(key), self).activated.connect(lambda: self.activate_button(self.pause_btn, self.toggle_play_pause))
        for key in KEYBOARD_SHORTCUTS["remove"]["keys"]:
            QShortcut(QKeySequence(key), self.playlist).activated.connect(lambda: self.activate_button(self.remove_btn, self.remove_file))
        for key in KEYBOARD_SHORTCUTS["play"]["playlist_keys"]:
            QShortcut(QKeySequence(key), self.playlist).activated.connect(lambda: self.activate_button(self.play_btn, self.play_media))
        self.sc_nav_prev = QShortcut(QKeySequence(navigation_shortcut("previous", False)), self)
        self.sc_nav_prev.activated.connect(lambda: self.activate_button(self.prev_btn, self.play_previous_file))
        self.sc_nav_next = QShortcut(QKeySequence(navigation_shortcut("next", False)), self)
        self.sc_nav_next.activated.connect(lambda: self.activate_button(self.next_btn, self.play_next_file))
        f_keys = {
            "search": self.search_input.setFocus,
            "focus_playlist": self.focus_first_track,
            "play": lambda: self.activate_button(self.play_btn, self.play_media),
            "stop": lambda: self.activate_button(self.stop_btn, self.stop_media),
            "previous": lambda: self.activate_button(self.prev_btn, self.play_previous_file),
            "next": lambda: self.activate_button(self.next_btn, self.play_next_file),
            "fade_out": lambda: self.activate_button(self.fade_btn, self.fade_out),
            "fullscreen": lambda: self.activate_button(self.fullscreen_btn, self.toggle_projection_fullscreen),
            "logo_audio": lambda: self.logo_audio_checkbox.setChecked(not self.logo_audio_checkbox.isChecked()),
            "logo_overlay": lambda: self.activate_button(self.logo_overlay_btn, lambda: self.logo_overlay_btn.setChecked(not self.logo_overlay_btn.isChecked())),
            "save_project": lambda: self.activate_button(self.save_proj_btn, self.save_project),
        }
        for name, callback in f_keys.items():
            for key in KEYBOARD_SHORTCUTS[name]["keys"]:
                QShortcut(QKeySequence(key), self).activated.connect(callback)
        self.update_shortcuts()

    def setup_button_feedback(self, *buttons):
        for button in buttons:
            button.setProperty("flash", False)
            button.clicked.connect(lambda checked=False, btn=button: self.flash_button(btn))

    def activate_button(self, button, callback):
        self.flash_button(button)
        callback()

    def flash_button(self, button):
        self.set_button_flash(button, True)
        QTimer.singleShot(180, lambda btn=button: self.set_button_flash(btn, False))

    def set_button_flash(self, button, enabled):
        if not button:
            return
        button.setProperty("flash", enabled)
        button.style().unpolish(button)
        button.style().polish(button)
        button.update()

    def focus_first_track(self):
        if self.proxy_model.rowCount() > 0:
            idx = self.proxy_model.index(0, 0)
            self.playlist.setCurrentIndex(idx)
            self.playlist.scrollTo(idx, QListView.ScrollHint.PositionAtTop)
            self.playlist.setFocus()

    def update_shortcut_descriptions(self):
        remote_enabled = self.remote_checkbox.isChecked()
        prev_shortcut = navigation_shortcut("previous", remote_enabled)
        next_shortcut = navigation_shortcut("next", remote_enabled)

        self.remove_btn.setText(f"✖ Usuń ({shortcut_label('remove')})")
        self.remove_btn.setToolTip(f"Usuń zaznaczone pliki ({shortcut_label('remove', tooltip=True)})")
        self.save_proj_btn.setText(f"💾 Zapisz Projekt ({shortcut_label('save_project')})")
        self.save_proj_btn.setToolTip(f"Zapisz aktualną listę ({shortcut_label('save_project')})")
        self.search_input.setPlaceholderText(f"🔍 Wyszukaj utwór po tytule... ({shortcut_label('search')})")

        self.prev_btn.setText(f"⏮ Poprzedni ({shortcut_label('previous', extra_keys=[prev_shortcut])})")
        self.prev_btn.setToolTip(f"Poprzedni plik ({shortcut_label('previous', extra_keys=[prev_shortcut], separator=' / ', tooltip=True)})")
        self.play_btn.setText(f"▶ PLAY ({shortcut_label('play', groups=('keys', 'playlist_keys'))})")
        self.play_btn.setToolTip(f"Odtwórz ({shortcut_label('play')})")
        self.pause_btn.setText(f"⏸ PAUSE ({shortcut_label('pause')})")
        self.pause_btn.setToolTip(f"Pauza / Wznów ({shortcut_label('pause')})")
        self.stop_btn.setText(f"⏹ STOP ({shortcut_label('stop')})")
        self.stop_btn.setToolTip(f"Zatrzymaj odtwarzanie ({shortcut_label('stop')})")
        self.next_btn.setText(f"Następny ⏭ ({shortcut_label('next', extra_keys=[next_shortcut])})")
        self.next_btn.setToolTip(f"Następny plik ({shortcut_label('next', extra_keys=[next_shortcut], separator=' / ', tooltip=True)})")

        self.fade_btn.setText(f"✨ Fade Out ({shortcut_label('fade_out')})")
        self.fade_btn.setToolTip(f"Płynne wyciszenie i ściemnienie ({shortcut_label('fade_out')})")
        self.fullscreen_btn.setText(f"📺 Pełny Ekran ({shortcut_label('fullscreen')})")
        self.fullscreen_btn.setToolTip(f"Przełącz pełny ekran ({shortcut_label('fullscreen')})")
        self.logo_audio_checkbox.setText(f"Obrazek dla Audio ({shortcut_label('logo_audio')})")
        self.logo_overlay_btn.setText(f"Nakładka na obraz ({shortcut_label('logo_overlay')})")

    def update_shortcuts(self):
        remote_enabled = self.remote_checkbox.isChecked()
        self.sc_nav_prev.setKey(QKeySequence(navigation_shortcut("previous", remote_enabled)))
        self.sc_nav_next.setKey(QKeySequence(navigation_shortcut("next", remote_enabled)))
        self.update_shortcut_descriptions()

    def set_volume(self, value):
        self.media_player.audio_set_volume(value)
        self.vol_label.setText(f"{value}%")

    def set_brightness(self, value):
        bri = value / 100.0
        self._set_projection_brightness(bri)
        self.bri_label.setText(f"{value}%")

    def _set_projection_brightness(self, brightness, queued=False):
        self.media_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, brightness)
        self.media_player.video_set_adjust_float(vlc.VideoAdjustOption.Contrast, brightness)
        if hasattr(self, 'logo_player'):
            self.logo_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, brightness)
            self.logo_player.video_set_adjust_float(vlc.VideoAdjustOption.Contrast, brightness)
        self.projection_window.logo_viewer.opacity = brightness

        if queued:
            QTimer.singleShot(0, self.projection_window.logo_viewer.update)
        else:
            self.projection_window.logo_viewer.update()

    def _on_fade_speed_changed(self, value):
        # value: 2–20, gdzie 10 = 1.0s, 20 = 2.0s
        seconds = value / 10.0
        self.fade_speed_label.setText(f"{seconds:.1f}s")

    def _fade_duration(self):
        """Zwraca czas trwania fade w sekundach (0.2 – 2.0)."""
        return self.fade_speed_slider.value() / 10.0

    def format_time(self, ms):
        s, _ = divmod(ms, 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

    def _check_logo_player_status(self):
        logo_path = getattr(self, '_logo_path', None)
        if logo_path and os.path.exists(logo_path) and not is_image_file(logo_path):
            if self.logo_player.get_state() in (vlc.State.Ended, vlc.State.Stopped):
                self.logo_player.play()
                self.logo_player.audio_set_volume(0)
                self.logo_player.audio_set_mute(True)

    def _update_media_player_progress(self):
        if self._is_current_playing_image() and self.image_autoplay_start is not None:
            elapsed = time.time() - self.image_autoplay_start
            total = self.image_autoplay_duration
            frac = min(1.0, elapsed / total) if total > 0 else 0.0
            self.progress_slider.setValue(int(frac * 1000))
            rem = max(0, int((total - elapsed) * 1000))
            self.time_label.setText(f"{self.format_time(int(elapsed * 1000))} / {self.format_time(int(total * 1000))} (Pozostało: -{self.format_time(rem)})")
        else:
            pos = self.media_player.get_position()
            if pos >= 0:
                self.progress_slider.setValue(int(pos * 1000))
            curr, total = self.media_player.get_time(), self.media_player.get_length()
            if curr >= 0 and total >= 0:
                rem = max(0, total - curr)
                self.time_label.setText(f"{self.format_time(curr)} / {self.format_time(total)} (Pozostało: -{self.format_time(rem)})")
                
                # Zabezpieczenie (self-healing): przesyłamy głośność z suwaka przez 
                # pierwsze 2 sekundy, co gwarantuje, że VLC poprawnie to odbierze
                if curr < 2000:
                    self.media_player.audio_set_volume(self.volume_slider.value())

    def check_player_status(self):
        try:
            self._check_logo_player_status()
            if self.is_playing and not self.is_transitioning:
                state = self.media_player.get_state()
                if state in (vlc.State.Ended, vlc.State.Stopped):
                    self.is_playing = False
                    if state == vlc.State.Ended and self.autoplay_checkbox.isChecked():
                        self.play_next_file()
                if not self.user_is_seeking:
                    self._update_media_player_progress()
            elif not self.user_is_seeking:
                self.progress_slider.setValue(0)
                self.time_label.setText(EMPTY_TIME_LABEL)
        except Exception:
            logging.error("Błąd w check_player_status:", exc_info=True)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Dodaj multimedia", "", MEDIA_FILE_FILTER)
        self.playlist_model.add_files(files)

    def remove_file(self):
        indexes = self.playlist.selectionModel().selectedIndexes()
        # Mapujemy indeksy z Proxy na model źródłowy
        source_indexes = [self.proxy_model.mapToSource(idx) for idx in indexes]
        rows = sorted(set(idx.row() for idx in source_indexes), reverse=True)
        for row in rows:
            self.playlist_model.removeRows(row, 1)

    def _move_selected_item(self, direction: int):
        """Przesuwa zaznaczony element o 1 pozycję w górę (direction=-1) lub dół (direction=+1)."""
        idx = self.playlist.currentIndex()
        if not idx.isValid():
            return
        source_idx = self.proxy_model.mapToSource(idx)
        src_row = source_idx.row()
        count = self.playlist_model.rowCount()
        dst_row = src_row + direction
        if dst_row < 0 or dst_row >= count:
            return
        # moveRows: destination jest "przed" wstawianym miejscem.
        # Przy przesunięciu w dół (sourceRow < destinationChild) model robi insert_row = destinationChild - 1,
        # więc aby element wylądował na dst_row, podajemy dst_row + 1.
        if direction > 0:
            self.playlist_model.moveRows(QModelIndex(), src_row, 1, QModelIndex(), dst_row + 1)
        else:
            self.playlist_model.moveRows(QModelIndex(), src_row, 1, QModelIndex(), dst_row)
        # Przywróć zaznaczenie na przeniesionym elemencie
        new_proxy_idx = self.proxy_model.mapFromSource(
            self.playlist_model.index(dst_row, 0)
        )
        self.playlist.setCurrentIndex(new_proxy_idx)

    def move_item_up(self):
        self._move_selected_item(-1)

    def move_item_down(self):
        self._move_selected_item(+1)



    def play_media(self):
        idx = self.playlist.currentIndex()
        if not idx.isValid() or self.is_transitioning:
            return
        source_idx = self.proxy_model.mapToSource(idx)
        row = source_idx.row()
        path = self.playlist_model.data(source_idx, Qt.ItemDataRole.UserRole)
        
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Błąd pliku", f"Plik nie istnieje lub został przeniesiony:\n{path}")
            return
            
        self._stop_image_autoplay_timer()
        self.playlist_model.set_playing_row(row)
        self._set_projection_mode_for_path(path)
        self._start_media_transition(path)
        if is_image_file(path):
            self._start_image_autoplay_timer()


    def _set_projection_mode_for_path(self, path):
        # Sprawdź globalny toggle oraz per-plik checkbox
        global_overlay = getattr(self, 'logo_overlay_btn', None) and self.logo_overlay_btn.isChecked()
        item_overlay = self.playlist_model.overlay_for_row(self.playlist_model.playing_row)
        if global_overlay or item_overlay:
            self.projection_window.set_mode_audio()
        elif path and is_audio_file(path) and self.logo_audio_checkbox.isChecked():
            self.projection_window.set_mode_audio()
        else:
            self.projection_window.set_mode_video()

    def _on_playlist_overlay_changed(self, top_left, bottom_right, roles=None):
        """Wywoływane gdy zmieni się CheckStateRole — od razu aktualizuje tryb projekcji
        jeśli zmodyfikowany wiersz jest właśnie odtwarzany."""
        if roles and Qt.ItemDataRole.CheckStateRole not in roles:
            return
        playing = self.playlist_model.playing_row
        if top_left.row() <= playing <= bottom_right.row():
            path = self._current_media_path()
            self._set_projection_mode_for_path(path)

    def _current_media_path(self):
        row = self.playlist_model.playing_row
        if row == -1:
            return None
        source_idx = self.playlist_model.index(row, 0)
        return self.playlist_model.data(source_idx, Qt.ItemDataRole.UserRole)

    def _start_image_autoplay_timer(self):
        self._stop_image_autoplay_timer()
        self.image_autoplay_duration = self.image_switch_delay.value()
        self.image_autoplay_start = time.time()
        self.image_autoplay_timer.start(self.image_autoplay_duration * 1000)

    def _stop_image_autoplay_timer(self):
        if self.image_autoplay_timer.isActive():
            self.image_autoplay_timer.stop()
        self.image_autoplay_start = None
        self.image_autoplay_duration = 0

    def _on_image_autoplay_timeout(self):
        if self.autoplay_checkbox.isChecked() and self._is_current_playing_image():
            self.play_next_file()

    def _on_autoplay_changed(self, state):
        if self._is_current_playing_image():
            if self.image_autoplay_start is None:
                self._start_image_autoplay_timer()
        else:
            self._stop_image_autoplay_timer()

    def _is_current_playing_image(self):
        return is_image_file(self._current_media_path())

    def _start_media_transition(self, path):
        self.is_transitioning = True
        try:
            self.media_player.stop()

            media = self.vlc_instance.media_new(path)
            self.media_player.set_media(media)
            self.media_player.play()
            self.is_playing = True
            QTimer.singleShot(100, self._finish_media_transition)
        except Exception:
            logging.error("Błąd podczas startu odtwarzania:", exc_info=True)
            self.is_transitioning = False

    def _finish_media_transition(self):
        try:
            self.media_player.video_set_adjust_int(vlc.VideoAdjustOption.Enable, 1)
            self._set_projection_brightness(self.brightness_slider.value() / 100.0)
            self.media_player.audio_set_mute(False)
        except Exception:
            logging.error("Błąd podczas finalizacji odtwarzania:", exc_info=True)
        finally:
            self.is_transitioning = False

    def fade_out(self):
        if self.is_playing and not self.is_transitioning:
            self._start_fade_out()

    def _is_current_playing_audio(self):
        return is_audio_file(self._current_media_path())

    def _start_fade_out(self):
        self.is_transitioning = True
        try:
            fade_secs = self._fade_duration()
            steps = max(5, int(fade_secs * 10))
            has_audio = (self.media_player.audio_get_track_count() > 0)
            audio_only = self._is_current_playing_audio()
            self._fade_state = {
                "step": 0,
                "steps": steps,
                "interval_ms": max(1, int((fade_secs * 1000) / steps)),
                "has_audio": has_audio,
                "audio_only": audio_only,
                "start_vol": self.media_player.audio_get_volume() if has_audio else 0,
                "start_bri": self.brightness_slider.value() / 100.0,
            }
            self.fade_timer.start(self._fade_state["interval_ms"])
        except Exception:
            logging.error("Błąd podczas startu fade out:", exc_info=True)
            self.is_transitioning = False

    def _fade_out_step(self):
        state = self._fade_state
        if not state:
            self.fade_timer.stop()
            return

        state["step"] += 1
        progress = min(1.0, state["step"] / state["steps"])

        if state["has_audio"]:
            vol = state["start_vol"] * (1 - progress)
            self.media_player.audio_set_volume(int(max(0, vol)))

        if not state["audio_only"]:
            bri = state["start_bri"] * (1 - progress)
            self._set_projection_brightness(max(0.0, bri))

        if progress >= 1.0:
            self.fade_timer.stop()
            self.stop_media(keep_logo=state["audio_only"], after_stop=self._finish_fade_out)

    def _finish_fade_out(self):
        state = self._fade_state
        if state and not state["audio_only"]:
            self._set_projection_brightness(state["start_bri"])
        self._fade_state = None
        self.is_transitioning = False

    def toggle_play_pause(self):
        if self.is_playing:
            if self.media_player.get_state() == vlc.State.Playing:
                self.media_player.pause()
            else:
                self.media_player.play()
        else:
            self.play_media()

    def stop_media(self, keep_logo=False, after_stop=None):
        self._stop_image_autoplay_timer()
        if self.fade_timer.isActive() and after_stop is None:
            self.fade_timer.stop()
            self._fade_state = None
            self.is_transitioning = False

        if self.media_player.get_state() in (vlc.State.Playing, vlc.State.Paused):
            # Odpinamy wideo przed audio (na czarny ekran) przed stopem
            if not keep_logo:
                self._set_projection_brightness(0.0)

            # Zerujemy odtwarzacz matematycznie, BEZ wyciszania gniazda sprzętowego
            has_audio = (self.media_player.audio_get_track_count() > 0)
            if has_audio:
                self.media_player.audio_set_volume(0)

            self.media_player.pause()
            QTimer.singleShot(50, lambda: self._finish_stop_media(after_stop))
            return

        self._finish_stop_media(after_stop)

    def _finish_stop_media(self, after_stop=None):
        self.media_player.stop()
        self.is_playing = False
        self.playlist_model.set_playing_row(-1)
        if after_stop:
            after_stop()

    def play_next_file(self):
        idx = self.playlist.currentIndex()
        if idx.isValid() and idx.row() < self.proxy_model.rowCount() - 1:
            new_idx = self.proxy_model.index(idx.row() + 1, 0)
            self.playlist.setCurrentIndex(new_idx)
            self.play_media()

    def play_previous_file(self):
        idx = self.playlist.currentIndex()
        if idx.isValid() and idx.row() > 0:
            new_idx = self.proxy_model.index(idx.row() - 1, 0)
            self.playlist.setCurrentIndex(new_idx)
            self.play_media()

    def select_logo(self):
        filter_str = "Wszystkie obsługiwane (*.png *.jpg *.jpeg *.bmp *.gif *.mp4 *.mkv);;Obrazy (*.png *.jpg *.jpeg *.bmp *.gif);;Wideo (*.mp4 *.mkv);;Wszystkie (*.*)"
        path, _ = QFileDialog.getOpenFileName(self, "Wybierz nakładkę", "", filter_str)
        if path:
            self._logo_path = path
            self.update_logo_media()

    def update_logo_media(self):
        path = getattr(self, '_logo_path', None)
        if not path or not os.path.exists(path):
            self.logo_player.stop()
            self.projection_window.logo_viewer.logo_pixmap = None
            self.projection_window.logo_viewer.update()
            return

        if is_image_file(path):
            self.logo_player.stop()
            self.projection_window.logo_viewer.logo_pixmap = QPixmap(path)
            self.projection_window.logo_stacked_layout.setCurrentWidget(self.projection_window.logo_viewer)
            self.projection_window.logo_viewer.update()
        else:
            self.projection_window.logo_viewer.logo_pixmap = None
            self.projection_window.logo_stacked_layout.setCurrentWidget(self.projection_window.logo_video_widget)
            media = self.vlc_instance.media_new(path)
            media.add_option('input-repeat=65535')
            self.logo_player.set_media(media)
            self.logo_player.play()
            self.logo_player.audio_set_volume(0)
            self.logo_player.audio_set_mute(True)
            self.logo_player.video_set_adjust_int(vlc.VideoAdjustOption.Enable, 1)
            bri = self.brightness_slider.value() / 100.0
            self.logo_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, bri)
            self.logo_player.video_set_adjust_float(vlc.VideoAdjustOption.Contrast, bri)

    def toggle_projection_fullscreen(self):
        if self.projection_window.isFullScreen():
            self.projection_window.showNormal()
        else:
            self.projection_window.showFullScreen()
        
        if sys.platform.startswith("win"):
            self.media_player.set_hwnd(int(self.projection_window.video_widget.winId()))
            self.logo_player.set_hwnd(int(self.projection_window.logo_video_widget.winId()))
            
        self.activateWindow()

    def toggle_projection_window(self):
        if self.projection_window.isVisible():
            self.projection_window.hide()
        else:
            self.projection_window.show()
            if sys.platform.startswith("win"):
                self.media_player.set_hwnd(int(self.projection_window.video_widget.winId()))
                self.logo_player.set_hwnd(int(self.projection_window.logo_video_widget.winId()))

    def toggle_logo_overlay(self, checked):
        if checked:
            self.projection_window.set_mode_audio()
        else:
            path = self._current_media_path()
            self._set_projection_mode_for_path(path) if path else self.projection_window.set_mode_video()

    def update_logo_visibility(self):
        self.projection_window.logo_viewer.show_logo = self.logo_audio_checkbox.isChecked()
        self.projection_window.logo_viewer.update()
        path = self._current_media_path()
        self._set_projection_mode_for_path(path)

    def set_position(self, v):
        self.media_player.set_position(v / 1000.0)

    def slider_released(self):
        self.user_is_seeking = False
        self.set_position(self.progress_slider.value())
    
    def filter_playlist(self, text):
        self.proxy_model.setFilterRegularExpression(text)

    def save_project(self):
        path, _ = QFileDialog.getSaveFileName(self, "Zapisz", "", PROJECT_FILE_FILTER)
        if path:
            try:
                files = [
                    {"path": item['path'], "overlay": item.get('overlay', False)}
                    for item in self.playlist_model._data
                ]
                project = {
                    "files": files,
                    "logo": getattr(self, '_logo_path', None)
                }
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(project, f, ensure_ascii=False, indent=4)
                self.settings.setValue("last_project", path)
                self.update_window_title(path)
            except Exception as e:
                QMessageBox.critical(self, "Błąd zapisu", f"Nie udało się zapisać projektu:\n{e}")

    def load_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "Wczytaj", "", PROJECT_FILE_FILTER)
        if path:
            self._load_project_file(path)
            
    def _load_project_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Obsługa 3 formatów:
            #   stary: lista ścieżek ["ścieżka", ...]
            #   pośredni: {"files": ["ścieżka", ...], "logo": ...}
            #   nowy:   {"files": [{"path": ..., "overlay": ...}, ...], "logo": ...}
            if isinstance(data, list):
                files_raw = data
                logo_path = None
            else:
                files_raw = data.get('files', [])
                logo_path = data.get('logo', None)
            
            self.playlist_model.clear()
            existing_files = []
            overlay_map = {}  # path -> bool
            for item in files_raw:
                if isinstance(item, str):
                    p, overlay = item, False
                else:
                    p = item.get('path', '')
                    overlay = item.get('overlay', False)
                if os.path.exists(p):
                    existing_files.append(p)
                    overlay_map[p] = overlay
                else:
                    print(f"Pominięto brakujący plik podczas wczytywania: {p}")
            
            self.playlist_model.add_files(existing_files)
            
            # Przywróć flagę nakładki dla każdego wczytanego pliku
            for i, entry in enumerate(self.playlist_model._data):
                entry['overlay'] = overlay_map.get(entry['path'], False)
            if self.playlist_model._data:
                self.playlist_model.dataChanged.emit(
                    self.playlist_model.index(0, 0),
                    self.playlist_model.index(len(self.playlist_model._data) - 1, 0)
                )
            
            if logo_path and os.path.exists(logo_path):
                self._logo_path = logo_path
                self.update_logo_media()
            
            self.settings.setValue("last_project", path)
            self.update_window_title(path)
        except Exception as e:
            QMessageBox.critical(self, "Błąd odczytu", f"Nie udało się wczytać projektu:\n{e}")

    def _on_theme_changed(self, _index):
        key = self.theme_combo.currentData()
        self.change_theme(key)

    def change_theme(self, theme_key: str):
        """Apply a new theme to the application and persist the choice."""
        if theme_key not in THEMES:
            theme_key = DEFAULT_THEME
        QApplication.instance().setStyleSheet(generate_stylesheet(theme_key))
        self.settings.setValue("theme", theme_key)

    def closeEvent(self, event):
        self.projection_window.close()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    settings = QSettings("ShowControl", "OperatorConsole")
    initial_theme = settings.value("theme", DEFAULT_THEME)
    app.setStyleSheet(generate_stylesheet(initial_theme))
    window = App()
    window.show()
    sys.exit(app.exec())
