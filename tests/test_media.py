"""Filtry dialogów plików i klasyfikacja mediów. Bez Qt i VLC."""

from showcontrol.domain.media import is_supported_media_file
from showcontrol.ui.i18n import (
    media_dialog_filter,
    overlay_dialog_filter,
    overlay_item_dialog_filter,
)

SUPPORTED_FORMATS = (
    ".mp4",
    ".mp3",
    ".mkv",
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".gif",
    ".wav",
    ".flac",
    ".aac",
    ".ogg",
    ".m4a",
)

OVERLAY_FORMATS = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".mp4", ".mkv")
AUDIO_FORMATS = (".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a")


def test_media_dialog_filter_offers_every_supported_format():
    for language in ("pl", "en"):
        filter_text = media_dialog_filter(language)
        for extension in SUPPORTED_FORMATS:
            assert is_supported_media_file(f"utwor{extension}"), extension
            assert f"*{extension}" in filter_text, (language, extension)
        assert "{" not in filter_text


def test_media_dialog_filter_keeps_all_files_option():
    assert media_dialog_filter("pl").endswith("Wszystkie (*.*)")
    assert media_dialog_filter("en").endswith("All files (*.*)")


def test_overlay_dialog_filter_offers_every_overlay_format():
    filter_text = overlay_dialog_filter("pl", "Nakładka")

    for extension in OVERLAY_FORMATS:
        assert f"*{extension}" in filter_text, extension
    for extension in AUDIO_FORMATS:
        assert f"*{extension}" not in filter_text, extension
    assert "Nakładka (" in filter_text
    assert "{" not in filter_text


def test_overlay_item_dialog_filter_offers_every_overlay_format():
    for language in ("pl", "en"):
        filter_text = overlay_item_dialog_filter(language)
        for extension in OVERLAY_FORMATS:
            assert f"*{extension}" in filter_text, (language, extension)
        for extension in AUDIO_FORMATS:
            assert f"*{extension}" not in filter_text, (language, extension)
        assert "{" not in filter_text
