"""Punkt startowy aplikacji: QApplication, QSettings, motyw i ikony."""

import logging
import os
import sys

# Wyciszenie nieszkodliwych ostrzeżeń Qt na Windowsie dotyczących obramowania okien
os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"

from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from showcontrol.ui.theme import DEFAULT_THEME, generate_stylesheet

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

SETTINGS_ORGANIZATION = "ShowControl"
SETTINGS_APPLICATION = "OperatorConsole"


def resource_path(filename):
    """Zwraca ścieżkę do zasobu w repo (dev) albo w katalogu PyInstallera."""
    base = getattr(sys, "_MEIPASS", None)
    if base is None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, filename)


def set_window_icon(widget, filename):
    path = resource_path(filename)
    if os.path.exists(path):
        widget.setWindowIcon(QIcon(path))
    else:
        print(f"Ostrzeżenie: Nie znaleziono pliku ikony pod adresem: {path}")


def create_application(argv):
    """Tworzy QApplication i pojedynczy QSettings, od razu nakłada motyw."""
    app = QApplication(argv)
    settings = QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
    theme_key = settings.value("theme", DEFAULT_THEME)
    app.setStyleSheet(generate_stylesheet(theme_key))
    return app, settings


def main():
    from showcontrol.app import App

    app, settings = create_application(sys.argv)
    window = App(settings)
    window.show()
    sys.exit(app.exec())
