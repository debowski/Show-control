"""Spójność tokenów motywów. Bez Qt: `theme.py` importuje Qt dopiero w środku."""

from showcontrol.ui.theme import DEFAULT_THEME, THEMES, THEME_KEYS, generate_stylesheet, theme_color


def test_every_theme_exposes_the_same_tokens():
    expected = set(THEMES[DEFAULT_THEME])

    for key in THEME_KEYS:
        assert set(THEMES[key]) == expected, key
        assert THEMES[key]["name"]


def test_theme_color_reads_the_requested_theme():
    for key in THEME_KEYS:
        assert theme_color("accent", key) == THEMES[key]["accent"]
        assert theme_color("list_play", key) == THEMES[key]["list_play"]


def test_stylesheet_uses_the_theme_tokens():
    for key in THEME_KEYS:
        qss = generate_stylesheet(key)
        for token in ("bg_main", "bg_dark", "accent", "text", "text_dim", "border", "play", "stop", "fade"):
            assert THEMES[key][token] in qss, (key, token)


def test_small_panel_labels_are_themed_by_qss():
    qss = generate_stylesheet("light")

    for object_name in ("MeterTitle", "PeakLabel", "VolumeTitle", "BrightnessTitle", "FadeTitle"):
        assert f"QLabel#{object_name}" in qss
    assert THEMES["light"]["text_dim"] in qss
