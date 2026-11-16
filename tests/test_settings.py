"""Menedżer ustawień: domyślne wartości i jawna lista kluczy. Bez Qt."""

import pytest

from showcontrol.persistence.settings import (DEFAULT_LANGUAGE, DEFAULT_THEME,
                                              SETTING_KEYS, QSettingsManager)
from showcontrol.ui.i18n import DEFAULT_LANGUAGE as I18N_DEFAULT_LANGUAGE
from showcontrol.ui.theme import DEFAULT_THEME as THEME_DEFAULT_THEME


class FakeSettings:
    """Zamiennik QSettings: tylko to, czego używa menedżer."""

    def __init__(self, values=None):
        self.values = dict(values or {})

    def value(self, key, default=None):
        return self.values.get(key, default)

    def setValue(self, key, value):
        self.values[key] = value


def test_defaults_come_from_their_single_sources():
    manager = QSettingsManager(FakeSettings())

    assert manager.get_theme() == THEME_DEFAULT_THEME
    assert manager.get_language() == I18N_DEFAULT_LANGUAGE
    assert manager.get_last_project() == ""
    assert DEFAULT_THEME is THEME_DEFAULT_THEME
    assert DEFAULT_LANGUAGE is I18N_DEFAULT_LANGUAGE


def test_injected_settings_object_is_used_directly():
    fake = FakeSettings()

    manager = QSettingsManager(fake)

    assert manager.settings is fake


def test_set_and_get_every_supported_key():
    fake = FakeSettings()
    manager = QSettingsManager(fake)

    manager.set_theme("light")
    manager.set_language("en")
    manager.set_last_project("C:/projekt.json")

    assert manager.get_theme() == "light"
    assert manager.get_language() == "en"
    assert manager.get_last_project() == "C:/projekt.json"
    assert fake.values == {
        "theme": "light",
        "language": "en",
        "last_project": "C:/projekt.json",
    }


def test_unknown_key_is_rejected_on_read():
    fake = FakeSettings({"obcy": "x"})
    manager = QSettingsManager(fake)

    with pytest.raises(KeyError):
        manager.value("obcy")
    assert fake.values["obcy"] == "x"


def test_unknown_key_is_rejected_on_write():
    fake = FakeSettings()
    manager = QSettingsManager(fake)

    with pytest.raises(KeyError):
        manager.set_value("obcy", "x")
    assert "obcy" not in fake.values


def test_setting_keys_are_explicit():
    assert SETTING_KEYS == ("theme", "language", "last_project")
