"""Ustawienia aplikacji z wyraźną listą kluczy."""

from __future__ import annotations

from PyQt6.QtCore import QSettings

SETTINGS_ORGANIZATION = "ShowControl"
SETTINGS_APPLICATION = "OperatorConsole"
SETTING_KEYS = ("theme", "language", "last_project")
DEFAULT_THEME = "dark"
DEFAULT_LANGUAGE = "pl"


class QSettingsManager:
    def __init__(self, org=SETTINGS_ORGANIZATION, app=SETTINGS_APPLICATION):
        self.settings = QSettings(org, app)

    def value(self, key, default=None):
        if key not in SETTING_KEYS:
            return self.settings.value(key, default)
        return self.settings.value(key, default)

    def set_value(self, key, value):
        if key not in SETTING_KEYS:
            raise KeyError(f"Nieobsługiwany klucz ustawień: {key}")
        self.settings.setValue(key, value)

    def get_theme(self):
        return self.value("theme", DEFAULT_THEME)

    def get_language(self):
        return self.value("language", DEFAULT_LANGUAGE)

    def get_last_project(self):
        return self.value("last_project", "")


def create_settings_manager(org=SETTINGS_ORGANIZATION, app=SETTINGS_APPLICATION):
    return QSettingsManager(org, app)
