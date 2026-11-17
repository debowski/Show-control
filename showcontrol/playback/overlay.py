"""Overlay: jeden załadowany asset i tryb projekcji. Bez UI konsoli."""

import os

from PyQt6.QtGui import QPixmap

from showcontrol.domain.media import is_image_file
from showcontrol.domain.overlay_rules import projection_plan
from showcontrol.playback.engine import vlc


class OverlayController:
    """Właściciel globalnego assetu, załadowanego assetu i trybu projekcji.

    `apply` rozstrzyga, co pokazać, i ładuje asset dokładnie raz na ścieżkę.
    `tick` zapętla wideo overlaya, gdy VLC samo go zatrzyma.
    """

    def __init__(self, engine, projection):
        self._engine = engine
        self._projection = projection
        self._global_asset = None
        self._loaded_asset = None
        self._overlay_mode = False

    @property
    def global_asset(self):
        return self._global_asset

    def set_global_asset(self, path):
        if path and os.path.exists(path):
            self._global_asset = path
            return True
        return False

    def apply(
        self,
        *,
        force_overlay_enabled,
        item_overlay_enabled,
        item_overlay_path,
        is_audio,
        overlay_on_audio_enabled,
        brightness,
    ):
        plan = projection_plan(
            force_overlay_enabled=force_overlay_enabled,
            item_overlay_enabled=item_overlay_enabled,
            item_overlay_path=item_overlay_path,
            is_audio=is_audio,
            overlay_on_audio_enabled=overlay_on_audio_enabled,
            global_overlay_path=self._global_asset,
        )

        show_overlay = plan.show_overlay
        state_changed = show_overlay != self._overlay_mode

        def commit():
            if show_overlay:
                # Asset first, then the mode switch: obraz jest gotowy, zanim
                # kurtyna się podniesie.
                self._load_asset(plan.asset_path, brightness)
                self._projection.set_mode_overlay()
            else:
                self._projection.set_mode_media()
            self._projection.overlay_viewer.show_overlay = show_overlay
            self._projection.overlay_viewer.update()

        if state_changed:
            self._overlay_mode = show_overlay
            is_global_overlay = (
                force_overlay_enabled
                or (is_audio and overlay_on_audio_enabled)
                or (show_overlay and plan.asset_path == self._global_asset)
                or (not show_overlay and self._loaded_asset == self._global_asset)
            )
            if is_global_overlay:
                if getattr(self._projection, "curtain", None):
                    self._projection.curtain.cancel()
                commit()
            else:
                ready_check = None
                if show_overlay and plan.asset_path and not is_image_file(plan.asset_path):
                    ready_check = self._engine.overlay_player.has_vout
                self._projection.fade_to(commit, ready_check)
        else:
            commit()
        return plan

    def tick(self):
        path = self._loaded_asset
        if path and os.path.exists(path) and not is_image_file(path):
            if self._engine.overlay_player.get_state() in (vlc.State.Ended, vlc.State.Stopped):
                self._engine.overlay_player.play()
                self._engine.mute_overlay()

    def _load_asset(self, path, brightness):
        if self._loaded_asset == path and path is not None:
            return  # Już załadowane, nie ma potrzeby restartować

        self._loaded_asset = path
        viewer = self._projection.overlay_viewer

        if not path or not os.path.exists(path):
            self._engine.overlay_player.stop()
            viewer.overlay_pixmap = None
            viewer.update()
            return

        if is_image_file(path):
            self._engine.overlay_player.stop()
            viewer.overlay_pixmap = QPixmap(path)
            self._projection.overlay_stacked_layout.setCurrentWidget(viewer)
            viewer.update()
        else:
            viewer.overlay_pixmap = None
            self._projection.overlay_stacked_layout.setCurrentWidget(self._projection.overlay_video_widget)
            media = self._engine.media(path)
            # Overlay media is always played without audio
            media.add_option(":no-audio")
            media.add_option("no-audio")
            media.add_option("input-repeat=65535")
            self._engine.overlay_player.set_media(media)
            self._engine.overlay_player.play()
            self._engine.mute_overlay()
            self._engine.overlay_player.video_set_adjust_int(vlc.VideoAdjustOption.Enable, 1)
            self._engine.set_overlay_brightness(brightness)
