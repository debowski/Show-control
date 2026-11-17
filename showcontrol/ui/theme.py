"""Tokeny motywów i generowanie arkusza QSS. Bez zależności od Qt."""

from __future__ import annotations

# Each theme is a flat dict of color tokens consumed by generate_stylesheet().
THEMES = {
    "dark": {
        "name": "Studio Dark",
        "bg_main": "#1e1e1e",
        "bg_dark": "#252526",
        "bg_btn": "#333333",
        "bg_hover": "#3e3e42",
        "accent": "#007acc",
        "accent_hi": "#005a9e",
        "flash_glow": "#6bbcff",
        "play": "#2d8a49",
        "play_hi": "#3aa659",
        "stop": "#a1260d",
        "stop_hi": "#be2d10",
        "fade": "#d18616",
        "fade_hi": "#e5951a",
        "hide": "#4a4a4a",
        "text": "#d4d4d4",
        "text_dim": "#aaaaaa",
        "border": "#3c3c3c",
        "list_play": "#094771",
    },
    "light": {
        "name": "Studio Light",
        "bg_main": "#f0f0f0",
        "bg_dark": "#e4e4e4",
        "bg_btn": "#dcdcdc",
        "bg_hover": "#c8c8c8",
        "accent": "#0063b1",
        "accent_hi": "#004e8a",
        "flash_glow": "#0078d7",
        "play": "#107c10",
        "play_hi": "#0e6b0e",
        "stop": "#c42b1c",
        "stop_hi": "#a52315",
        "fade": "#ca5010",
        "fade_hi": "#b8460e",
        "hide": "#8a8a8a",
        "text": "#1a1a1a",
        "text_dim": "#555555",
        "border": "#b0b0b0",
        "list_play": "#cce4f7",
    },
    "stealth": {
        "name": "Red Night (Stealth)",
        "bg_main": "#0a0000",
        "bg_dark": "#120000",
        "bg_btn": "#200000",
        "bg_hover": "#2e0000",
        "accent": "#cc0000",
        "accent_hi": "#990000",
        "flash_glow": "#ff4444",
        "play": "#8b0000",
        "play_hi": "#a00000",
        "stop": "#4a0000",
        "stop_hi": "#5e0000",
        "fade": "#7a3000",
        "fade_hi": "#8e3800",
        "hide": "#1e0000",
        "text": "#cc4444",
        "text_dim": "#883333",
        "border": "#3a0000",
        "list_play": "#330000",
    },
    "broadcast": {
        "name": "Broadcast Indigo",
        "bg_main": "#12131f",
        "bg_dark": "#1a1b2e",
        "bg_btn": "#252640",
        "bg_hover": "#32335a",
        "accent": "#6c63ff",
        "accent_hi": "#4b44cc",
        "flash_glow": "#a89cff",
        "play": "#2ecc71",
        "play_hi": "#27ae60",
        "stop": "#e74c3c",
        "stop_hi": "#c0392b",
        "fade": "#f39c12",
        "fade_hi": "#d68910",
        "hide": "#3d3d5c",
        "text": "#e8e8ff",
        "text_dim": "#9999cc",
        "border": "#3a3a5c",
        "list_play": "#1e1f40",
    },
}

THEME_KEYS = list(THEMES.keys())
DEFAULT_THEME = "dark"


def active_theme_key() -> str:
    try:
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is not None:
            theme_key = app.property("theme_key")
            if isinstance(theme_key, str) and theme_key in THEMES:
                return theme_key
    except Exception:
        pass
    return DEFAULT_THEME


def theme_color(token: str, theme_key: str | None = None) -> str:
    selected_key = theme_key or active_theme_key()
    theme = THEMES.get(selected_key, THEMES[DEFAULT_THEME])
    return theme.get(token, THEMES[DEFAULT_THEME].get(token, "#ffffff"))


def generate_stylesheet(theme_key: str) -> str:
    """Build and return a full QSS stylesheet for the given theme key."""
    t = THEMES.get(theme_key, THEMES[DEFAULT_THEME])
    return f"""
    QMainWindow, QWidget {{
        background-color: {t["bg_main"]};
        color: {t["text"]};
        font-family: 'Segoe UI', system-ui;
        font-size: 10pt;
    }}

    QGroupBox {{
        border: 1px solid {t["border"]};
        border-radius: 4px;
        margin-top: 1.2em;
        font-weight: bold;
        color: {t["accent"]};
        padding: 10px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
    }}

    /* --- Buttons base --- */
    QPushButton {{
        background-color: {t["bg_btn"]};
        color: {t["text"]};
        border: 1px solid {t["border"]};
        padding: 8px 15px;
        border-radius: 3px;
        min-height: 22px;
    }}
    QPushButton:hover  {{ background-color: {t["bg_hover"]}; }}
    QPushButton:pressed {{ background-color: {t["accent"]}; color: white; }}
    QPushButton:checked {{
        background-color: {t["accent"]};
        color: white;
        font-weight: bold;
        border: 1px solid {t["accent_hi"]};
    }}

    /* --- Transport buttons --- */
    QPushButton#PlayBtn {{
        background-color: {t["play"]};
        color: white;
        font-weight: bold;
        font-size: 11pt;
        min-height: 45px;
    }}
    QPushButton#PlayBtn:hover  {{ background-color: {t["play_hi"]}; }}

    QPushButton#StopBtn {{
        background-color: {t["stop"]};
        color: white;
        font-weight: bold;
        font-size: 11pt;
        min-height: 45px;
    }}
    QPushButton#StopBtn:hover  {{ background-color: {t["stop_hi"]}; }}

    QPushButton#TransportBtn {{
        font-weight: bold;
        min-height: 45px;
    }}

    QPushButton#FadeBtn {{
        background-color: {t["fade"]};
        color: white;
    }}
    QPushButton#FadeBtn:hover  {{ background-color: {t["fade_hi"]}; }}

    QPushButton#HideBtn {{
        background-color: {t["hide"]};
        color: {t["text_dim"]};
    }}

    /* --- Flash state (all named variants) --- */
    QPushButton[flash="true"] {{
        background-color: {t["accent"]};
        color: white;
        border: 2px solid {t["flash_glow"]};
        font-weight: bold;
    }}

    /* --- Lists --- */
    QListView {{
        background-color: {t["bg_dark"]};
        border: 1px solid {t["border"]};
        outline: none;
        alternate-background-color: {t["bg_main"]};
    }}
    QListView::item:hover {{
        background-color: {t["bg_hover"]};
    }}
    QListView::item:selected {{
        background-color: {t["accent"]};
        color: white;
    }}

    /* --- Inputs --- */
    QLineEdit, QSpinBox, QComboBox {{
        background-color: {t["bg_dark"]};
        border: 1px solid {t["border"]};
        color: {t["text"]};
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
        border-left: 1px solid {t["border"]};
        border-bottom: 1px solid {t["border"]};
        border-top-right-radius: 3px;
        background-color: {t["bg_btn"]};
    }}
    QSpinBox::down-button {{
        subcontrol-origin: border;
        subcontrol-position: bottom right;
        width: 18px;
        border-left: 1px solid {t["border"]};
        border-bottom-right-radius: 3px;
        background-color: {t["bg_btn"]};
    }}
    QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
        background-color: {t["bg_hover"]};
    }}
    QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {{
        background-color: {t["accent"]};
    }}
    QSpinBox::up-arrow {{
        width: 7px; height: 7px;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-bottom: 5px solid {t["text_dim"]};
    }}
    QSpinBox::down-arrow {{
        width: 7px; height: 7px;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid {t["text_dim"]};
    }}
    QSpinBox::up-arrow:hover, QSpinBox::down-arrow:hover {{
        border-bottom-color: {t["accent"]};
        border-top-color: {t["accent"]};
    }}

    QComboBox::drop-down {{ border: none; }}
    QComboBox QAbstractItemView {{
        background-color: {t["bg_dark"]};
        color: {t["text"]};
        selection-background-color: {t["accent"]};
    }}

    /* --- Sliders --- */
    QSlider::groove:horizontal {{
        border: 1px solid {t["border"]};
        height: 8px;
        background: {t["bg_dark"]};
        border-radius: 4px;
    }}
    QSlider::handle:horizontal {{
        background: {t["accent"]};
        width: 18px;
        height: 18px;
        margin: -6px 0;
        border-radius: 9px;
    }}
    QSlider::groove:vertical {{
        border: 1px solid {t["border"]};
        width: 8px;
        background: {t["bg_dark"]};
        border-radius: 4px;
    }}
    QSlider::handle:vertical {{
        background: {t["accent"]};
        width: 18px;
        height: 18px;
        margin: 0 -6px;
        border-radius: 9px;
    }}

    /* --- Scrollbars --- */
    QScrollBar:vertical {{
        background: {t["bg_dark"]};
        width: 10px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical {{
        background: {t["border"]};
        border-radius: 5px;
        min-height: 20px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

    /* --- Screen warning banner --- */
    QLabel#ScreenWarningLabel {{
        background-color: {t["bg_dark"]};
        color: {t["fade"]};
        border: 1px solid {t["fade"]};
        border-radius: 4px;
        padding: 6px 10px;
        font-weight: bold;
    }}

    /* --- Time label --- */
    QLabel#TimeLabel {{
        font-size: 13pt;
        font-weight: bold;
        color: {t["text"]};
    }}

    /* --- Small labels above sliders and the meter --- */
    QLabel#MeterTitle, QLabel#PeakLabel, QLabel#VolumeTitle,
    QLabel#BrightnessTitle, QLabel#FadeTitle {{
        font-size: 8pt;
        color: {t["text_dim"]};
    }}
    QLabel#PeakLabel {{
        font-family: monospace;
    }}

    /* --- Move buttons (lista) --- */
    QPushButton#MoveBtn {{
        background-color: transparent;
        color: {t["text_dim"]};
        border: 1px solid transparent;
        border-radius: 4px;
        font-size: 9pt;
        padding: 0px;
    }}
    QPushButton#MoveBtn:hover {{
        background-color: {t["bg_hover"]};
        color: {t["accent"]};
        border: 1px solid {t["border"]};
    }}
    QPushButton#MoveBtn:pressed {{
        background-color: {t["accent"]};
        color: white;
    }}
    """
