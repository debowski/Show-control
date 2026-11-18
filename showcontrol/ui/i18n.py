"""Teksty interfejsu PL/EN. Bez zależności od Qt."""

from showcontrol.domain.media import (
    IMAGE_EXTENSIONS,
    MEDIA_EXTENSIONS,
    OVERLAY_EXTENSIONS,
    VIDEO_EXTENSIONS,
)

# Prosty mechanizm tłumaczeń (polski / angielski)
DEFAULT_LANGUAGE = "pl"
TRANSLATIONS = {
    "pl": {
        "projection_window_title": "Projekcja - Odtwarzacz",
        "add_files": "✚ Dodaj pliki",
        "add_files_tooltip": "Dodaj nowe pliki do listy",
        "load_project": "📂 Wczytaj Projekt",
        "load_project_tooltip": "Wczytaj zapisaną listę plików",
        "save_project": "💾 Zapisz Projekt",
        "save_project_tooltip": "Zapisz aktualną listę",
        "select_overlay": "📁 Wybierz overlay",
        "select_overlay_tooltip": "Wybierz obraz lub grafikę wyświetlaną jako overlay",
        "clear_overlay": "🗑 Wyczyść overlay",
        "clear_overlay_tooltip": "Usuń globalny overlay z projekcji",
        "overlay_status_none": "Overlay: brak",
        "overlay_status": "Overlay: {name}",
        "screen_warning": "⚠ Tylko jeden ekran — okno projekcji działa jako okno 800×600 na konsoli operatora. Podłącz drugi ekran, a projekcja przejdzie na niego automatycznie.",
        "toggle_projection": "👁 Ukryj Okno",
        "toggle_projection_tooltip": "Ukryj lub pokaż okno projekcji",
        "search_placeholder": "🔍 Wyszukaj utwór po tytule...",
        "playback_control": "Kontrola odtwarzania",
        "view_effects": "Widok i Efekty",
        "control": "Sterowanie",
        "settings": "Ustawienia",
        "spectrum_analyzer": "Analizator widma",
        "meter": "📊 Miernik",
        "peak_meter_tooltip": "Miernik szczytowy stereo (IEC dBFS)",
        "volume": "🔊 Głośność",
        "fade": "⏱ Fade",
        "brightness": "💡 Jasność",
        "image_speed": "⏱ Prędkość grafiki",
        "image_speed_tooltip": "Czas wyświetlania plików graficznych w sekundach przy autoodtwarzaniu",
        "move_up_tooltip": "Przesuń plik w górę",
        "move_down_tooltip": "Przesuń plik w dół",
        "brightness_tooltip": "Jasność okna projekcji (0% – 100%)",
        "fade_tooltip": "Czas trwania efektu fade (0.0s – 1.0s)",
        "remote_mode": "Tryb Pilota (L/P)",
        "autoplay": "Autoodtwarzanie",
        "theme": "🎨 Motyw",
        "remove_short": "✖ Usuń",
        "previous_short": "⏮ Poprzedni",
        "play_short": "▶ PLAY",
        "pause_short": "⏸ PAUSE",
        "stop_short": "⏹ STOP",
        "next_short": "Następny ⏭",
        "fade_out": "✨ Fade Out",
        "fullscreen": "📺 Pełny Ekran",
        "overlay_on_audio": "Overlay przy audio",
        "force_overlay": "Wymuś overlay",
        "force_overlay_tooltip": "Pokaż overlay globalny i zasłoń media oraz overlay pozycji",
        "force_overlay_disabled": "Wybierz plik nakładki, aby użyć F9",
        "overlay_migration_title": "Overlay pozycji",
        "overlay_migration_message": "{count} pozycji miało włączony overlay bez własnego pliku. Flaga została wyczyszczona — checkbox oznacza teraz wyłącznie własny overlay.",
        "language": "Język",
        "key_delete_short": "Del",
        "key_delete_long": "Delete",
        "key_down_short": "↓",
        "key_down_long": "Strzałka w dół",
        "key_enter_short": "Enter",
        "key_enter_long": "Enter",
        "key_left_short": "←",
        "key_left_long": "Strzałka w lewo",
        "key_right_short": "→",
        "key_right_long": "Strzałka w prawo",
        "key_space_short": "Spacja",
        "key_space_long": "Spacja",
        "key_up_short": "↑",
        "key_up_long": "Strzałka w górę",
        "empty_time_label": "00:00 / 00:00 (Pozostało: -00:00)",
        "time_status": "{elapsed} / {total} (Pozostało: -{remaining})",
        "add_media_dialog": "Dodaj multimedia",
        "select_overlay_dialog": "Wybierz nakładkę",
        "save_dialog": "Zapisz",
        "load_dialog": "Wczytaj",
        "media_filter": "Media ({patterns});;Wszystkie (*.*)",
        "project_filter": "JSON (*.json)",
        "overlay_filter": "{title} ({patterns});;{title} ({image_patterns});;{title} ({video_patterns});;Wszystkie (*.*)",
        "overlay_item_filter": "Wszystkie obsługiwane ({patterns});;Obrazy ({image_patterns});;Wideo ({video_patterns});;Wszystkie (*.*)",
        "overlay_item_tooltip": "[nakładka: {name}]",
        "overlay_global_tooltip": "[nakładka globalna]",
        "file_error_title": "Błąd pliku",
        "file_missing": "Plik nie istnieje lub został przeniesiony:\n{path}",
        "skipped_missing_file": "Pominięto brakujący plik podczas wczytywania: {path}",
        "save_error_title": "Błąd zapisu",
        "save_failed": "Nie udało się zapisać projektu:\n{error}",
        "load_error_title": "Błąd odczytu",
        "load_failed": "Nie udało się wczytać projektu:\n{error}",
    },
    "en": {
        "projection_window_title": "Projection - Player",
        "add_files": "✚ Add files",
        "add_files_tooltip": "Add new files to the list",
        "load_project": "📂 Load Project",
        "load_project_tooltip": "Load a saved file list",
        "save_project": "💾 Save Project",
        "save_project_tooltip": "Save the current list",
        "select_overlay": "📁 Select overlay file",
        "select_overlay_tooltip": "Choose an image or graphic to display",
        "clear_overlay": "🗑 Clear overlay",
        "clear_overlay_tooltip": "Remove the global overlay from projection",
        "overlay_status_none": "Overlay: none",
        "overlay_status": "Overlay: {name}",
        "screen_warning": "⚠ Only one screen — the projection window runs as an 800×600 window on the operator console. Connect a second screen and the projection moves there automatically.",
        "toggle_projection": "👁 Toggle Window",
        "toggle_projection_tooltip": "Hide or show the projection window",
        "search_placeholder": "🔍 Search track by title...",
        "playback_control": "Playback Control",
        "view_effects": "View & Effects",
        "control": "Control",
        "settings": "Settings",
        "spectrum_analyzer": "Spectrum Analyzer",
        "meter": "📊 Meter",
        "peak_meter_tooltip": "Stereo peak meter (IEC dBFS)",
        "volume": "🔊 Volume",
        "fade": "⏱ Fade",
        "brightness": "💡 Brightness",
        "image_speed": "⏱ Image Speed",
        "image_speed_tooltip": "Image display time in seconds during autoplay",
        "move_up_tooltip": "Move file up",
        "move_down_tooltip": "Move file down",
        "brightness_tooltip": "Projection window brightness (0% – 100%)",
        "fade_tooltip": "Fade duration (0.0s – 1.0s)",
        "remote_mode": "Remote Mode (L/P)",
        "autoplay": "Autoplay",
        "theme": "🎨 Theme",
        "remove_short": "✖ Remove",
        "previous_short": "⏮ Previous",
        "play_short": "▶ PLAY",
        "pause_short": "⏸ PAUSE",
        "stop_short": "⏹ STOP",
        "next_short": "Next ⏭",
        "fade_out": "✨ Fade Out",
        "fullscreen": "📺 Fullscreen",
        "overlay_on_audio": "Overlay on audio",
        "force_overlay": "Force overlay",
        "force_overlay_tooltip": "Show the global overlay and cover media and the item overlay",
        "force_overlay_disabled": "Select an overlay file to use F9",
        "overlay_migration_title": "Item overlay",
        "overlay_migration_message": "{count} items had the overlay flag without their own file. The flag was cleared — the checkbox now means only a per-item overlay.",
        "language": "Language",
        "key_delete_short": "Del",
        "key_delete_long": "Delete",
        "key_down_short": "↓",
        "key_down_long": "Arrow down",
        "key_enter_short": "Enter",
        "key_enter_long": "Enter",
        "key_left_short": "←",
        "key_left_long": "Arrow left",
        "key_right_short": "→",
        "key_right_long": "Arrow right",
        "key_space_short": "Space",
        "key_space_long": "Space",
        "key_up_short": "↑",
        "key_up_long": "Arrow up",
        "empty_time_label": "00:00 / 00:00 (Remaining: -00:00)",
        "time_status": "{elapsed} / {total} (Remaining: -{remaining})",
        "add_media_dialog": "Add media",
        "select_overlay_dialog": "Select overlay",
        "save_dialog": "Save",
        "load_dialog": "Load",
        "media_filter": "Media ({patterns});;All files (*.*)",
        "project_filter": "JSON (*.json)",
        "overlay_filter": "{title} ({patterns});;{title} ({image_patterns});;{title} ({video_patterns});;All files (*.*)",
        "overlay_item_filter": "All supported ({patterns});;Images ({image_patterns});;Video ({video_patterns});;All files (*.*)",
        "overlay_item_tooltip": "[overlay: {name}]",
        "overlay_global_tooltip": "[global overlay]",
        "file_error_title": "File Error",
        "file_missing": "File does not exist or has been moved:\n{path}",
        "skipped_missing_file": "Skipped missing file while loading: {path}",
        "save_error_title": "Save Error",
        "save_failed": "Could not save the project:\n{error}",
        "load_error_title": "Load Error",
        "load_failed": "Could not load the project:\n{error}",
    },
}

# Adding a language means adding a TRANSLATIONS entry and its display name.
LANGUAGE_NAMES = {"pl": "Polski", "en": "English"}
LANGUAGE_KEYS = tuple(TRANSLATIONS)

VLC_MISSING_MESSAGE = (
    "Błąd: Biblioteka python-vlc nie jest zainstalowana. Zainstaluj ją używając: pip install python-vlc"
)


def get_t(language, key, **kwargs):
    """Zwraca tekst dla danego języka; klucz nieznany wraca jako własna nazwa."""
    table = TRANSLATIONS.get(language, TRANSLATIONS[DEFAULT_LANGUAGE])
    text = table.get(key, TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key))
    try:
        return text.format(**kwargs)
    except Exception:
        return text


def _patterns(extensions):
    """Maska rozszerzeń dla QFileDialog, np. ``*.mp4 *.mkv``."""
    return " ".join(f"*{extension}" for extension in extensions)


_MEDIA_PATTERNS = _patterns(MEDIA_EXTENSIONS)
_OVERLAY_PATTERNS = _patterns(OVERLAY_EXTENSIONS)
_IMAGE_PATTERNS = _patterns(IMAGE_EXTENSIONS)
_VIDEO_PATTERNS = _patterns(VIDEO_EXTENSIONS)


def media_dialog_filter(language):
    """Filtr dialogu dodawania mediów oparty na `MEDIA_EXTENSIONS`."""
    return get_t(language, "media_filter", patterns=_MEDIA_PATTERNS)


def overlay_dialog_filter(language, title):
    """Filtr dialogu wyboru globalnego overlaya (obrazy i wideo)."""
    return get_t(
        language,
        "overlay_filter",
        title=title,
        patterns=_OVERLAY_PATTERNS,
        image_patterns=_IMAGE_PATTERNS,
        video_patterns=_VIDEO_PATTERNS,
    )


def overlay_item_dialog_filter(language):
    """Filtr dialogu wyboru overlaya pozycji (obrazy i wideo)."""
    return get_t(
        language,
        "overlay_item_filter",
        patterns=_OVERLAY_PATTERNS,
        image_patterns=_IMAGE_PATTERNS,
        video_patterns=_VIDEO_PATTERNS,
    )
