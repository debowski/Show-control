"""Okno operatora: spina silnik, sesję, overlay i widoki.

Logika VLC, fade i transportu żyje w ``playback/``. Tutaj zostaje wyłącznie
sklejenie modułów, obsługa zdarzeń UI i zapis/odczyt projektu.
"""

import os
import sys

from PyQt6.QtCore import QModelIndex, Qt, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (QApplication, QFileDialog, QListView,
                             QMainWindow, QMessageBox)

from showcontrol import __version__
from showcontrol.bootstrap import set_window_icon
from showcontrol.domain.media import is_audio_file
from showcontrol.domain.project_schema import Project, ProjectItem
from showcontrol.persistence.project_io import load_project_file, save_project_file
from showcontrol.playback.engine import Engine
from showcontrol.playback.fade import FadeController
from showcontrol.playback.overlay import OverlayController
from showcontrol.playback.session import PlaybackSession
from showcontrol.ui.i18n import DEFAULT_LANGUAGE, get_t as translate
from showcontrol.ui.layout import build_main_layout
from showcontrol.ui.peak_meter import AudioPeakProvider
from showcontrol.ui.playlist_view import PlaylistModel
from showcontrol.ui.projection import ProjectionWindow
from showcontrol.ui.shortcuts import (KEYBOARD_SHORTCUTS, navigation_shortcut,
                                      shortcut_description)
from showcontrol.ui.theme import DEFAULT_THEME, THEMES, generate_stylesheet


def main(argv=None):
    """Punkt wejścia aplikacji zgodny z fazą 1 refaktoru."""
    from showcontrol.bootstrap import create_application

    app, settings = create_application(sys.argv if argv is None else argv)
    window = MainWindow(settings)
    window.show()
    sys.exit(app.exec())


class MainWindow(QMainWindow):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.base_title = f"Show Control - Operator Console v{__version__}"
        self.setWindowTitle(self.base_title)
        self.setMinimumSize(900, 700)

        set_window_icon(self, "ikona_sc.ico")

        try:
            self.engine = Engine()
        except Exception as e:
            QMessageBox.critical(self, "VLC Error", f"VLC Error: {e}")
            sys.exit(1)

        self.projection_window = ProjectionWindow()
        self.projection_window.move_to_second_screen()
        self.projection_window.show()
        self.engine.attach(self.projection_window.video_widget,
                           self.projection_window.overlay_video_widget)

        self.playlist_model = PlaylistModel(self)
        self.overlay = OverlayController(self.engine, self.projection_window)
        self._last_progress = None
        self.session = PlaybackSession(
            self.engine, self.playlist_model.store,
            advance=self.play_next_file,
            overlay_tick=self.overlay.tick,
            parent=self,
        )
        self.session.playing_row_changed.connect(self.playlist_model.set_playing_row)
        self.session.media_changed.connect(self._set_projection_mode_for_path)
        self.session.progress_changed.connect(self._on_progress)
        self.session.idle.connect(self._on_idle)
        self.session.stopping.connect(self._on_stopping)
        self.session.transition_finished.connect(self._on_transition_finished)
        self.playlist_model.rowsInserted.connect(self.session.on_rows_inserted)
        self.playlist_model.rowsRemoved.connect(self.session.on_rows_removed)
        self.playlist_model.rowsMoved.connect(self.session.on_rows_moved)
        self.playlist_model.modelReset.connect(self.session.on_model_reset)

        self.init_ui()
        self.fade = FadeController(self.engine, self._set_projection_brightness, parent=self)
        self.fade.finished.connect(self._on_fade_finished)
        self.audio_peak_provider = AudioPeakProvider()
        self._meter_timer = QTimer(self)
        self._meter_timer.setInterval(30)
        self._meter_timer.timeout.connect(self._update_audio_meter)
        self._meter_timer.start()
        self.session.start()

        last_project = self.settings.get_last_project()
        if last_project and os.path.exists(last_project):
            # Używamy QTimer by załadować projekt po pełnym zainicjalizowaniu UI
            QTimer.singleShot(100, lambda: self._load_project_file(last_project))

    def update_window_title(self, path):
        if path:
            name = os.path.basename(path)
            self.setWindowTitle(f"{self.base_title} - [{name}]")
        else:
            self.setWindowTitle(self.base_title)

    def init_ui(self):
        build_main_layout(self)

    def init_shortcuts(self):
        for key in KEYBOARD_SHORTCUTS["pause"]["keys"]:
            QShortcut(QKeySequence(key), self).activated.connect(lambda: self.activate_button(self.pause_btn, self.toggle_play_pause))
        for key in KEYBOARD_SHORTCUTS["remove"]["keys"]:
            QShortcut(QKeySequence(key), self.playlist).activated.connect(lambda: self.activate_button(self.remove_btn, self.remove_file))
        for key in KEYBOARD_SHORTCUTS["play"]["playlist_keys"]:
            QShortcut(QKeySequence(key), self.playlist).activated.connect(lambda: self.activate_button(self.play_btn, self.play_media))
        self.sc_nav_prev = QShortcut(QKeySequence(navigation_shortcut("previous", False)), self)
        self.sc_nav_prev.activated.connect(lambda: self.activate_button(self.prev_btn, self.play_previous_file))
        self.sc_nav_next = QShortcut(QKeySequence(navigation_shortcut("next", False)), self)
        self.sc_nav_next.activated.connect(lambda: self.activate_button(self.next_btn, self.play_next_file))
        f_keys = {
            "search": self.search_input.setFocus,
            "focus_playlist": self.focus_first_track,
            "play": lambda: self.activate_button(self.play_btn, self.play_media),
            "stop": lambda: self.activate_button(self.stop_btn, self.stop_media),
            "previous": lambda: self.activate_button(self.prev_btn, self.play_previous_file),
            "next": lambda: self.activate_button(self.next_btn, self.play_next_file),
            "fade_out": lambda: self.activate_button(self.fade_btn, self.fade_out),
            "fullscreen": lambda: self.activate_button(self.fullscreen_btn, self.toggle_projection_fullscreen),
            "overlay_on_audio": lambda: self.overlay_on_audio_checkbox.setChecked(not self.overlay_on_audio_checkbox.isChecked()),
            "force_overlay": lambda: self.activate_button(self.force_overlay_btn, lambda: self.force_overlay_btn.setChecked(not self.force_overlay_btn.isChecked())),
            "save_project": lambda: self.activate_button(self.save_proj_btn, self.save_project),
        }
        for name, callback in f_keys.items():
            for key in KEYBOARD_SHORTCUTS[name]["keys"]:
                QShortcut(QKeySequence(key), self).activated.connect(callback)
        self.update_shortcuts()

    def get_t(self, key, **kwargs):
        """Return translated string for current language, formatting with kwargs if provided."""
        return translate(getattr(self, 'language', DEFAULT_LANGUAGE), key, **kwargs)

    def apply_translations(self):
        """Apply translations to visible UI widgets. Safe to call multiple times."""
        self.projection_window.setWindowTitle(self.get_t('projection_window_title'))

        self.add_btn.setText(self.get_t('add_files'))
        self.add_btn.setToolTip(self.get_t('add_files_tooltip'))
        self.load_proj_btn.setText(self.get_t('load_project'))
        self.load_proj_btn.setToolTip(self.get_t('load_project_tooltip'))
        self.overlay_btn.setText(self.get_t('select_overlay'))
        self.overlay_btn.setToolTip(self.get_t('select_overlay_tooltip'))
        self.window_btn.setText(self.get_t('toggle_projection'))
        self.window_btn.setToolTip(self.get_t('toggle_projection_tooltip'))

        self.transport_group.setTitle(self.get_t('playback_control'))
        self.view_group.setTitle(self.get_t('view_effects'))
        self.audio_group.setTitle(self.get_t('control'))
        self.settings_group.setTitle(self.get_t('settings'))

        self.meter_title.setText(self.get_t('meter'))
        self.peak_meter.setToolTip(self.get_t('peak_meter_tooltip'))
        self.volume_title.setText(self.get_t('volume'))
        self.brightness_title.setText(self.get_t('brightness'))
        self.fade_title.setText(self.get_t('fade'))
        self.image_speed_title.setText(self.get_t('image_speed'))
        self.theme_label.setText(self.get_t('theme'))
        self.lang_label.setText(self.get_t('language'))

        self.move_up_btn.setToolTip(self.get_t('move_up_tooltip'))
        self.move_down_btn.setToolTip(self.get_t('move_down_tooltip'))
        self.image_switch_delay.setToolTip(self.get_t('image_speed_tooltip'))
        self.brightness_slider.setToolTip(self.get_t('brightness_tooltip'))
        self.fade_speed_slider.setToolTip(self.get_t('fade_tooltip'))

        self.autoplay_checkbox.setText(self.get_t('autoplay'))
        self.remote_checkbox.setText(self.get_t('remote_mode'))

        self._refresh_time_label()
        self.update_shortcut_descriptions()

    def _on_language_changed(self, index):
        key = self.lang_combo.currentData()
        if not key:
            return
        self.language = key
        self.settings.set_language(key)
        self.apply_translations()

    def setup_button_feedback(self, *buttons):
        for button in buttons:
            button.setProperty("flash", False)
            button.clicked.connect(lambda checked=False, btn=button: self.flash_button(btn))

    def activate_button(self, button, callback):
        self.flash_button(button)
        callback()

    def flash_button(self, button):
        self.set_button_flash(button, True)
        QTimer.singleShot(180, lambda btn=button: self.set_button_flash(btn, False))

    def set_button_flash(self, button, enabled):
        if not button:
            return
        button.setProperty("flash", enabled)
        button.style().unpolish(button)
        button.style().polish(button)
        button.update()

    def focus_first_track(self):
        if self.proxy_model.rowCount() > 0:
            idx = self.proxy_model.index(0, 0)
            self.playlist.setCurrentIndex(idx)
            self.playlist.scrollTo(idx, QListView.ScrollHint.PositionAtTop)
            self.playlist.setFocus()

    def update_shortcut_descriptions(self):
        """Jedyne miejsce, które wpisuje etykiety z klawiszami do widżetów."""
        remote_enabled = self.remote_checkbox.isChecked()
        language = getattr(self, 'language', DEFAULT_LANGUAGE)
        prev_key = navigation_shortcut("previous", remote_enabled)
        next_key = navigation_shortcut("next", remote_enabled)

        def description(name, tooltip=False, **kwargs):
            return shortcut_description(
                name, language=language, tooltip=tooltip, **kwargs
            )

        def apply(widget, name, tooltip_kwargs=None, **kwargs):
            widget.setText(description(name, **kwargs))
            tooltip_args = dict(kwargs) if tooltip_kwargs is None else tooltip_kwargs
            tooltip = description(name, tooltip=True, **tooltip_args)
            if tooltip is not None:
                widget.setToolTip(tooltip)

        self.search_input.setPlaceholderText(description('search'))
        apply(self.remove_btn, 'remove')
        apply(self.save_proj_btn, 'save_project')
        apply(self.prev_btn, 'previous', extra_keys=[prev_key],
              tooltip_kwargs={'extra_keys': [prev_key], 'separator': ' / '})
        apply(self.play_btn, 'play', groups=('keys', 'playlist_keys'),
              tooltip_kwargs={})
        apply(self.pause_btn, 'pause')
        apply(self.stop_btn, 'stop')
        apply(self.next_btn, 'next', extra_keys=[next_key],
              tooltip_kwargs={'extra_keys': [next_key], 'separator': ' / '})
        apply(self.fade_btn, 'fade_out')
        apply(self.fullscreen_btn, 'fullscreen')
        self.overlay_on_audio_checkbox.setText(
            description('overlay_on_audio')
        )
        self.force_overlay_btn.setText(description('force_overlay'))
        self._sync_force_overlay_control()

    def update_shortcuts(self):
        remote_enabled = self.remote_checkbox.isChecked()
        self.sc_nav_prev.setKey(QKeySequence(navigation_shortcut("previous", remote_enabled)))
        self.sc_nav_next.setKey(QKeySequence(navigation_shortcut("next", remote_enabled)))
        self.update_shortcut_descriptions()

    def set_volume(self, value):
        self.session.set_volume(value)
        self.vol_label.setText(f"{value}%")

    def set_brightness(self, value):
        bri = value / 100.0
        self._set_projection_brightness(bri)
        self.bri_label.setText(f"{value}%")

    def _set_projection_brightness(self, brightness, queued=False):
        self.engine.set_brightness(brightness)
        self.projection_window.overlay_viewer.opacity = brightness

        if queued:
            QTimer.singleShot(0, self.projection_window.overlay_viewer.update)
        else:
            self.projection_window.overlay_viewer.update()

    def _on_fade_speed_changed(self, value):
        # value: 0–10, gdzie 10 = 1.0s
        seconds = value / 10.0
        self.fade_speed_label.setText(f"{seconds:.1f}s")

    def _fade_duration(self):
        """Zwraca czas trwania fade w sekundach (0.0 – 1.0)."""
        return self.fade_speed_slider.value() / 10.0

    def format_time(self, ms):
        s, _ = divmod(ms, 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

    def _refresh_time_label(self):
        if self._last_progress is None:
            self.time_label.setText(self.get_t('empty_time_label'))
            return
        elapsed_ms, total_ms = self._last_progress
        remaining_ms = max(0, total_ms - elapsed_ms)
        self.time_label.setText(self.get_t(
            'time_status',
            elapsed=self.format_time(elapsed_ms),
            total=self.format_time(total_ms),
            remaining=self.format_time(remaining_ms),
        ))

    def _on_progress(self, fraction, elapsed_ms, total_ms):
        if fraction >= 0:
            self.progress_slider.setValue(int(fraction * 1000))
        if elapsed_ms >= 0 and total_ms >= 0:
            self._last_progress = (elapsed_ms, total_ms)
            self._refresh_time_label()

            # Zabezpieczenie (self-healing): przesyłamy głośność z suwaka przez
            # pierwsze 2 sekundy, co gwarantuje, że VLC poprawnie to odbierze
            if elapsed_ms < 2000:
                self.engine.player.audio_set_volume(self.volume_slider.value())

    def _update_audio_meter(self):
        is_playing = self.session.is_playing and not self.session.is_transitioning
        if self.session.is_current_image():
            is_playing = False
        db_l, db_r = self.audio_peak_provider.get_levels(is_playing, self.session.volume)
        self.peak_meter.set_levels(db_l, db_r)

    def _on_peak_changed(self, peak_db):
        if peak_db <= -59.5:
            self.meter_peak_label.setText("-∞ dBFS")
        else:
            self.meter_peak_label.setText(f"{peak_db:.1f} dB")

    def _on_idle(self):
        self.progress_slider.setValue(0)
        self._last_progress = None
        self._refresh_time_label()
        self.peak_meter.reset()

    def _on_stopping(self, keep_overlay):
        if not keep_overlay:
            self._set_projection_brightness(0.0)

    def _on_transition_finished(self):
        self._set_projection_brightness(self.brightness_slider.value() / 100.0)

    def add_files(self):
        title = self.get_t('add_media_dialog')
        files, _ = QFileDialog.getOpenFileNames(
            self, title, "", self.get_t('media_filter')
        )
        self.playlist_model.add_files(files)

    def remove_file(self):
        indexes = self.playlist.selectionModel().selectedIndexes()
        # Mapujemy indeksy z Proxy na model źródłowy
        source_indexes = [self.proxy_model.mapToSource(idx) for idx in indexes]
        rows = sorted(set(idx.row() for idx in source_indexes), reverse=True)
        for row in rows:
            self.playlist_model.removeRows(row, 1)

    def _move_selected_item(self, direction: int):
        """Przesuwa zaznaczony element o 1 pozycję w górę (direction=-1) lub dół (direction=+1)."""
        idx = self.playlist.currentIndex()
        if not idx.isValid():
            return
        source_idx = self.proxy_model.mapToSource(idx)
        src_row = source_idx.row()
        count = self.playlist_model.rowCount()
        dst_row = src_row + direction
        if dst_row < 0 or dst_row >= count:
            return
        # moveRows: destination jest "przed" wstawianym miejscem.
        # Przy przesunięciu w dół (sourceRow < destinationChild) model robi insert_row = destinationChild - 1,
        # więc aby element wylądował na dst_row, podajemy dst_row + 1.
        if direction > 0:
            self.playlist_model.moveRows(QModelIndex(), src_row, 1, QModelIndex(), dst_row + 1)
        else:
            self.playlist_model.moveRows(QModelIndex(), src_row, 1, QModelIndex(), dst_row)
        # Przywróć zaznaczenie na przeniesionym elemencie
        new_proxy_idx = self.proxy_model.mapFromSource(
            self.playlist_model.index(dst_row, 0)
        )
        self.playlist.setCurrentIndex(new_proxy_idx)

    def move_item_up(self):
        self._move_selected_item(-1)

    def move_item_down(self):
        self._move_selected_item(+1)



    def play_media(self):
        idx = self.playlist.currentIndex()
        if not idx.isValid() or self.session.is_transitioning:
            return
        source_idx = self.proxy_model.mapToSource(idx)
        row = source_idx.row()
        path = self.playlist_model.data(source_idx, Qt.ItemDataRole.UserRole)

        if not path or not os.path.exists(path):
            QMessageBox.warning(self, self.get_t('file_error_title'), self.get_t('file_missing', path=path))
            return

        self.session.play_row(row, self.image_switch_delay.value())


    def _set_projection_mode_for_path(self, path):
        self.overlay.apply(
            force_overlay_enabled=bool(
                getattr(self, 'force_overlay_btn', None)
                and self.force_overlay_btn.isChecked()
            ),
            item_overlay_enabled=self.playlist_model.overlay_for_row(self.session.playing_row),
            item_overlay_path=self.playlist_model.overlay_path_for_row(self.session.playing_row),
            is_audio=bool(path and is_audio_file(path)),
            overlay_on_audio_enabled=self.overlay_on_audio_checkbox.isChecked(),
            brightness=self.brightness_slider.value() / 100.0,
        )

    def _on_playlist_overlay_changed(self, top_left, bottom_right, roles=None):
        """Wywoływane gdy zmieni się CheckStateRole lub inne istotne dane — od razu aktualizuje tryb projekcji
        jeśli zmodyfikowany wiersz jest właśnie odtwarzany."""
        if roles and (Qt.ItemDataRole.CheckStateRole not in roles and Qt.ItemDataRole.UserRole + 1 not in roles):
            return
        playing = self.session.playing_row
        if top_left.row() <= playing <= bottom_right.row():
            path = self.session.current_media_path()
            self._set_projection_mode_for_path(path)

    def _on_autoplay_changed(self, state):
        self.session.set_autoplay(
            self.autoplay_checkbox.isChecked(), self.image_switch_delay.value()
        )

    def fade_out(self):
        if not self.session.is_playing or self.session.is_transitioning:
            return
        self.session.begin_transition()
        if not self.fade.start(
            self._fade_duration(),
            self.brightness_slider.value() / 100.0,
            self.session.is_current_audio(),
        ):
            self.session.end_transition()

    def _on_fade_finished(self, audio_only, start_brightness):
        self.session.stop(
            keep_overlay=audio_only,
            after_stop=lambda: self._after_fade_stop(audio_only, start_brightness),
        )

    def _after_fade_stop(self, audio_only, start_brightness):
        if not audio_only:
            self._set_projection_brightness(start_brightness)
        self.session.end_transition()

    def toggle_play_pause(self):
        if not self.session.toggle_play_pause():
            self.play_media()

    def stop_media(self, keep_overlay=False, after_stop=None):
        if self.fade.is_active and after_stop is None:
            self.fade.cancel()
            self.session.end_transition()

        self.session.stop(keep_overlay=keep_overlay, after_stop=after_stop)

    def play_next_file(self):
        idx = self.playlist.currentIndex()
        if idx.isValid() and idx.row() < self.proxy_model.rowCount() - 1:
            new_idx = self.proxy_model.index(idx.row() + 1, 0)
            self.playlist.setCurrentIndex(new_idx)
            self.play_media()

    def play_previous_file(self):
        idx = self.playlist.currentIndex()
        if idx.isValid() and idx.row() > 0:
            new_idx = self.proxy_model.index(idx.row() - 1, 0)
            self.playlist.setCurrentIndex(new_idx)
            self.play_media()

    def select_overlay(self):
        title = self.get_t('select_overlay_dialog')
        filter_str = self.get_t('overlay_filter', title=title)
        path, _ = QFileDialog.getOpenFileName(self, title, "", filter_str)
        if path:
            self.overlay.set_global_asset(path)
            self._sync_force_overlay_control()
            self._set_projection_mode_for_path(self.session.current_media_path())

    def toggle_projection_fullscreen(self):
        if self.projection_window.isFullScreen():
            self.projection_window.showNormal()
        else:
            self.projection_window.showFullScreen()

        self.engine.attach(self.projection_window.video_widget,
                           self.projection_window.overlay_video_widget)

        self.activateWindow()

    def toggle_projection_window(self):
        if self.projection_window.isVisible():
            self.projection_window.hide()
        else:
            self.projection_window.show()
            self.engine.attach(self.projection_window.video_widget,
                               self.projection_window.overlay_video_widget)

    def toggle_overlay(self, checked):
        if checked and not self.overlay.global_asset:
            self.force_overlay_btn.setChecked(False)
            return
        path = self.session.current_media_path()
        self._set_projection_mode_for_path(path)

    def _sync_force_overlay_control(self):
        enabled = bool(self.overlay.global_asset)
        if not enabled and self.force_overlay_btn.isChecked():
            self.force_overlay_btn.setChecked(False)
        self.force_overlay_btn.setEnabled(enabled)
        key = 'force_overlay_tooltip' if enabled else 'force_overlay_disabled'
        self.force_overlay_btn.setToolTip(self.get_t(key))

    def update_overlay_visibility(self):
        path = self.session.current_media_path()
        self._set_projection_mode_for_path(path)

    def filter_playlist(self, text):
        self.proxy_model.setFilterRegularExpression(text)

    def save_project(self):
        path, _ = QFileDialog.getSaveFileName(
            self, self.get_t('save_dialog'), "", self.get_t('project_filter')
        )
        if path:
            try:
                project = Project(
                    items=tuple(
                        ProjectItem(entry.path, entry.overlay, entry.overlay_path)
                        for entry in self.playlist_model.entries()
                    ),
                    overlay_path=self.overlay.global_asset,
                )
                save_project_file(path, project)
                self.settings.set_last_project(path)
                self.update_window_title(path)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    self.get_t('save_error_title'),
                    self.get_t('save_failed', error=e),
                )

    def load_project(self):
        path, _ = QFileDialog.getOpenFileName(
            self, self.get_t('load_dialog'), "", self.get_t('project_filter')
        )
        if path:
            self._load_project_file(path)

    def _load_project_file(self, path):
        try:
            project = load_project_file(path)
            self.force_overlay_btn.setChecked(False)

            if project.migrated_overlay_count:
                QMessageBox.information(
                    self,
                    self.get_t('overlay_migration_title'),
                    self.get_t('overlay_migration_message',
                              count=project.migrated_overlay_count),
                )

            self.playlist_model.clear()
            existing_files = []
            overlay_map = {}  # path -> (bool, overlay_path)
            for item in project.items:
                if os.path.exists(item.path):
                    existing_files.append(item.path)
                    overlay_map[item.path] = (item.overlay, item.overlay_path)
                else:
                    print(self.get_t('skipped_missing_file', path=item.path))

            self.playlist_model.add_files(existing_files)

            # Przywróć flagę i ścieżkę nakładki dla każdego wczytanego pliku
            for row, entry in enumerate(self.playlist_model.entries()):
                overlay, overlay_path = overlay_map.get(entry.path, (False, None))
                self.playlist_model.set_overlay_state(row, overlay, overlay_path)
            if existing_files:
                self.playlist_model.refresh_rows(0, len(existing_files) - 1)

            if project.overlay_path and os.path.exists(project.overlay_path):
                self.overlay.set_global_asset(project.overlay_path)

            self._sync_force_overlay_control()
            self._set_projection_mode_for_path(self.session.current_media_path())

            self.settings.set_last_project(path)
            self.update_window_title(path)
        except Exception as e:
            QMessageBox.critical(
                self,
                self.get_t('load_error_title'),
                self.get_t('load_failed', error=e),
            )

    def _on_theme_changed(self, _index):
        key = self.theme_combo.currentData()
        self.change_theme(key)

    def change_theme(self, theme_key: str):
        """Apply a new theme to the application and persist the choice."""
        if theme_key not in THEMES:
            theme_key = DEFAULT_THEME
        app = QApplication.instance()
        app.setProperty("theme_key", theme_key)
        app.setStyleSheet(generate_stylesheet(theme_key))
        # Delegate and BackgroundRole read tokens during paint, so repaint now.
        self.playlist.viewport().update()
        self.settings.set_theme(theme_key)

    def closeEvent(self, event):
        self.projection_window.close()
        super().closeEvent(event)
