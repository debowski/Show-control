"""Teksty interfejsu PL/EN. Bez zależności od Qt."""

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
        "select_overlay": "📁 Wybierz plik nakładki",
        "select_overlay_tooltip": "Wybierz obrazek lub grafikę do wyświetlania",
        "toggle_projection": "👁 Ukryj Okno",
        "toggle_projection_tooltip": "Ukryj lub pokaż okno projekcji",
        "search_placeholder": "🔍 Wyszukaj utwór po tytule...",
        "playback_control": "Kontrola odtwarzania",
        "view_effects": "Widok i Efekty",
        "control": "Sterowanie",
        "settings": "Ustawienia",
        "volume": "🔊 Głośność",
        "fade": "⏱ Fade",
        "brightness": "💡 Jasność",
        "image_speed": "⏱ Prędkość grafiki",
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
        "overlay_on_audio": "Obrazek dla Audio",
        "force_overlay": "Nakładka na obraz",
        "language": "Język",
        "add_media_dialog": "Dodaj multimedia",
        "select_overlay_dialog": "Wybierz nakładkę",
        "save_dialog": "Zapisz",
        "load_dialog": "Wczytaj",
        "file_error_title": "Błąd pliku",
        "file_missing": "Plik nie istnieje lub został przeniesiony:\n{path}",
        "save_error_title": "Błąd zapisu",
        "load_error_title": "Błąd odczytu",
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
        "toggle_projection": "👁 Toggle Window",
        "toggle_projection_tooltip": "Hide or show the projection window",
        "search_placeholder": "🔍 Search track by title...",
        "playback_control": "Playback Control",
        "view_effects": "View & Effects",
        "control": "Control",
        "settings": "Settings",
        "volume": "🔊 Volume",
        "fade": "⏱ Fade",
        "brightness": "💡 Brightness",
        "image_speed": "⏱ Image Speed",
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
        "overlay_on_audio": "Image for Audio",
        "force_overlay": "Overlay on image",
        "language": "Language",
        "add_media_dialog": "Add media",
        "select_overlay_dialog": "Select overlay",
        "save_dialog": "Save",
        "load_dialog": "Load",
        "file_error_title": "File Error",
        "file_missing": "File does not exist or has been moved:\n{path}",
        "save_error_title": "Save Error",
        "load_error_title": "Load Error",
    }
}

VLC_MISSING_MESSAGE = ("Błąd: Biblioteka python-vlc nie jest zainstalowana. "
                       "Zainstaluj ją używając: pip install python-vlc")


def get_t(language, key, **kwargs):
    """Zwraca tekst dla danego języka; klucz nieznany wraca jako własna nazwa."""
    table = TRANSLATIONS.get(language, TRANSLATIONS[DEFAULT_LANGUAGE])
    text = table.get(key, TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key))
    try:
        return text.format(**kwargs)
    except Exception:
        return text
