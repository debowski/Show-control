"""Ustawienia aplikacji z wyraźną listą kluczy."""

from __future__ import annotations

from showcontrol.ui.i18n import DEFAULT_LANGUAGE
from showcontrol.ui.theme import DEFAULT_THEME

SETTINGS_ORGANIZATION = "ShowControl"
SETTINGS_APPLICATION = "OperatorConsole"
SETTING_KEYS = ("theme", "language", "last_project")


class QSettingsManager:
    """Cienka warstwa nad QSettings z jawną listą dozwolonych kluczy.

    Można wstrzyknąć gotowy obiekt QSettings (albo zgodny zamiennik), dzięki
    czemu warstwa ustawień jest testowalna bez uruchamiania Qt.
    """

    def __init__(self, settings=None, *, org=SETTINGS_ORGANIZATION, app=SETTINGS_APPLICATION):
        if settings is None:
            from PyQt6.QtCore import QSettings

            settings = QSettings(org, app)
        self.settings = settings

    @staticmethod
    def _require_key(key):
        if key not in SETTING_KEYS:
            raise KeyError(f"Nieobsługiwany klucz ustawień: {key}")

    def value(self, key, default=None):
        self._require_key(key)
        return self.settings.value(key, default)

    def set_value(self, key, value):
        self._require_key(key)
        self.settings.setValue(key, value)

    def get_theme(self):
        return self.value("theme", DEFAULT_THEME)

    def set_theme(self, theme):
        self.set_value("theme", theme)

    def get_language(self):
        return self.value("language", DEFAULT_LANGUAGE)

    def set_language(self, language):
        self.set_value("language", language)

    def get_last_project(self):
        return self.value("last_project", "")

    def set_last_project(self, path):
        self.set_value("last_project", path)


def create_settings_manager(org=SETTINGS_ORGANIZATION, app=SETTINGS_APPLICATION):
    return QSettingsManager(org=org, app=app)
