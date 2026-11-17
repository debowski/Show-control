"""Silnik odtwarzania: instancja VLC i dwa odtwarzacze (Windows-only)."""

import sys

from showcontrol.ui.i18n import VLC_MISSING_MESSAGE

try:
    import vlc
except ImportError:
    print(VLC_MISSING_MESSAGE)
    sys.exit(1)


class Engine:
    """Właściciel `vlc.Instance` i dwóch `MediaPlayerów`: głównego i overlaya.

    Nie zna playlisty ani projektu. Osadzanie w oknie projekcji (`hwnd`),
    głośność, jasność i wyciszenie overlaya należą tutaj.
    """

    def __init__(self):
        self.instance = vlc.Instance("--no-xlib", "--quiet", "--video-filter=adjust")
        self.player = self.instance.media_player_new()
        self.player.audio_set_volume(0)  # Konfiguracja zabezpieczająca na start
        self.player.video_set_adjust_int(vlc.VideoAdjustOption.Enable, 1)
        self.overlay_player = self.instance.media_player_new()
        self.overlay_player.audio_output_set("adummy")
        self.overlay_player.audio_set_volume(0)
        self.overlay_player.video_set_adjust_int(vlc.VideoAdjustOption.Enable, 1)

    def media(self, path):
        """Tworzy media dla ścieżki; wspólne dla obu odtwarzaczy."""
        return self.instance.media_new(path)

    def attach(self, video_widget, overlay_widget):
        """Osadza odtwarzacze w widżetach okna projekcji."""
        self.player.set_hwnd(int(video_widget.winId()))
        self.overlay_player.set_hwnd(int(overlay_widget.winId()))
        for player in (self.player, self.overlay_player):
            player.video_set_mouse_input(False)
            player.video_set_key_input(False)

    def set_volume(self, value):
        """Głośność głównego odtwarzacza; overlay jest zawsze wyciszony."""
        self.player.audio_set_volume(value)

    def set_brightness(self, brightness):
        """Jasność i kontrast obu odtwarzaczy."""
        self._apply_brightness(self.player, brightness)
        self._apply_brightness(self.overlay_player, brightness)

    def set_overlay_brightness(self, brightness):
        self._apply_brightness(self.overlay_player, brightness)

    def mute_overlay(self):
        self.overlay_player.audio_set_volume(0)

    @staticmethod
    def _apply_brightness(player, brightness):
        player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, brightness)
        player.video_set_adjust_float(vlc.VideoAdjustOption.Contrast, brightness)
