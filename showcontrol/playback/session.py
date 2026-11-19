"""Sesja odtwarzania: co teraz gra, co dalej i przejścia. Bez UI."""

import logging
import time
from dataclasses import dataclass

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from showcontrol.domain.media import is_audio_file, is_image_file
from showcontrol.domain.playlist import (
    adjust_row_for_insert,
    adjust_row_for_move,
    adjust_row_for_remove,
    next_autoplay_row,
    previous_autoplay_row,
)
from showcontrol.playback.engine import vlc


@dataclass
class SessionState:
    """Stan sesji. Jedyne miejsce, w które faza B podepnie recovery."""

    playing_row: int = -1
    is_playing: bool = False
    is_transitioning: bool = False
    user_is_seeking: bool = False
    volume: int = 100


class PlaybackSession(QObject):
    """Właściciel stanu „co teraz gra" i transportu.

    UI komunikuje się wyłącznie przez sygnały: `playing_row_changed` odświeża
    podświetlenie, `media_changed` ustawia tryb projekcji, `progress_changed`
    rysuje pasek i czas, `idle` zeruje je, `stopping` pozwala wyzerować
    jasność, a `transition_finished` ją przywrócić.
    `playing_row_removed` znaczy „usunięto bieżący wiersz" — transport
    zatrzymuje okno, bo tylko ono zna fade i jasność.
    `failure` jest seamem recovery dla fazy B.
    """

    playing_row_changed = pyqtSignal(int)
    playing_row_removed = pyqtSignal()
    media_changed = pyqtSignal(str)
    progress_changed = pyqtSignal(float, int, int)
    idle = pyqtSignal()
    stopping = pyqtSignal(bool)
    transition_finished = pyqtSignal()
    failure = pyqtSignal(str)

    def __init__(self, engine, store, overlay_tick=None, on_failure=None, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.store = store
        self.state = SessionState()
        self.autoplay_enabled = False
        self.image_autoplay_start = None
        self.image_autoplay_duration = 0
        # Czas obrazu z UI dla kolejnych pozycji; `image_autoplay_duration`
        # to migawka aktywnego timera bieżącego obrazu.
        self.configured_image_duration = 0
        self._overlay_tick = overlay_tick
        self._on_failure = on_failure

        self._image_timer = QTimer(self)
        self._image_timer.setSingleShot(True)
        self._image_timer.timeout.connect(self._on_image_timeout)
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._poll)

    # --- stan ---

    @property
    def playing_row(self):
        return self.state.playing_row

    @property
    def is_playing(self):
        return self.state.is_playing

    @property
    def is_transitioning(self):
        return self.state.is_transitioning

    @property
    def user_is_seeking(self):
        return self.state.user_is_seeking

    @property
    def volume(self):
        return self.state.volume

    def current_media_path(self):
        row = self.state.playing_row
        if 0 <= row < self.store.row_count():
            return self.store.path_at(row)
        return None

    def is_current_image(self):
        return is_image_file(self.current_media_path())

    def is_current_audio(self):
        return is_audio_file(self.current_media_path())

    def is_audio_rendering(self):
        """Czy bieżąca pozycja naprawdę oddaje dźwięk do urządzenia.

        ``is_playing`` zostaje prawdziwe w pauzie, a obraz nie ma ścieżki
        audio, więc miernik nie może oprzeć się na samej fladze sesji.
        Fade out nadal gra, dlatego flaga przejścia nie wyłącza pomiaru.
        """
        if not self.state.is_playing or self.is_current_image():
            return False
        return self.engine.player.get_state() == vlc.State.Playing

    # --- cykl życia ---

    def start(self):
        self._status_timer.start(500)

    def shutdown(self):
        self._status_timer.stop()
        self._stop_image_autoplay()

    # --- transport ---

    def play_row(self, row, image_duration_seconds):
        if self.state.is_transitioning:
            return False

        path = self.store.path_at(row)
        self.configured_image_duration = image_duration_seconds
        self._stop_image_autoplay()
        self._set_playing_row(row)
        self.media_changed.emit(path)
        self._start_media_transition(path)
        if is_image_file(path):
            self._start_image_autoplay(image_duration_seconds)
        return True

    def play_next(self):
        """W trybie autoplay: następny wiersz, po ostatnim zawija na pierwszy."""
        if not self.autoplay_enabled:
            return
        self._play_adjacent(next_autoplay_row)

    def play_previous(self):
        """W trybie autoplay: poprzedni wiersz; na pierwszym nie ma dokąd cofać."""
        if not self.autoplay_enabled:
            return
        self._play_adjacent(previous_autoplay_row)

    def _play_adjacent(self, choose_row):
        row = choose_row(self.state.playing_row, self.store.row_count())
        if row >= 0:
            self.play_row(row, self.configured_image_duration)

    def toggle_play_pause(self):
        """Pauza/wznowienie; `False` znaczy „nie ma czego wznawiać"."""
        if not self.state.is_playing:
            return False
        if self.engine.player.get_state() == vlc.State.Playing:
            self.engine.player.pause()
        else:
            self.engine.player.play()
        return True

    def stop(self, keep_overlay=False, after_stop=None):
        self._stop_image_autoplay()
        if self.engine.player.get_state() in (vlc.State.Playing, vlc.State.Paused):
            # Odpinamy wideo przed audio (na czarny ekran) przed stopem
            self.stopping.emit(keep_overlay)

            # Zerujemy odtwarzacz matematycznie, BEZ wyciszania gniazda sprzętowego
            has_audio = self.engine.player.audio_get_track_count() > 0
            if has_audio:
                self.engine.player.audio_set_volume(0)

            self.engine.player.pause()
            QTimer.singleShot(50, lambda: self._finish_stop(after_stop))
            return

        self._finish_stop(after_stop)

    def _finish_stop(self, after_stop):
        self.engine.player.stop()
        self.state.is_playing = False
        self._set_playing_row(-1)
        if after_stop:
            after_stop()

    def _start_media_transition(self, path):
        self.state.is_transitioning = True
        try:
            self.engine.player.stop()

            media = self.engine.media(path)
            self.engine.player.set_media(media)
            self.engine.player.play()
            self.state.is_playing = True
            QTimer.singleShot(100, self._finish_media_transition)
        except Exception as exc:
            logging.error("Błąd podczas startu odtwarzania:", exc_info=True)
            self.state.is_transitioning = False
            self._report_failure(exc)

    def _finish_media_transition(self):
        try:
            self.engine.player.video_set_adjust_int(vlc.VideoAdjustOption.Enable, 1)
            self.transition_finished.emit()
            self.engine.player.audio_set_mute(False)
        except Exception as exc:
            logging.error("Błąd podczas finalizacji odtwarzania:", exc_info=True)
            self._report_failure(exc)
        finally:
            self.state.is_transitioning = False

    def begin_transition(self):
        """Blokada przejścia dla fade'a (w fazie 3 przejmie ją FadeController)."""
        self.state.is_transitioning = True

    def end_transition(self):
        self.state.is_transitioning = False

    # --- seek ---

    def begin_seek(self):
        self.state.user_is_seeking = True

    def set_position(self, value):
        self.engine.player.set_position(value / 1000.0)

    def end_seek(self, value):
        self.state.user_is_seeking = False
        self.set_position(value)

    # --- głośność ---

    def set_volume(self, value):
        self.state.volume = value
        self.engine.set_volume(value)

    # --- autoplay ---

    def set_image_duration(self, image_duration_seconds):
        """Czas ekspozycji dla kolejnych obrazów; bieżącego timera nie rusza."""
        self.configured_image_duration = image_duration_seconds

    def set_autoplay(self, enabled, image_duration_seconds):
        self.autoplay_enabled = enabled
        self.set_image_duration(image_duration_seconds)
        if self.is_current_image():
            if self.image_autoplay_start is None:
                self._start_image_autoplay(image_duration_seconds)
        else:
            self._stop_image_autoplay()

    def _start_image_autoplay(self, duration_seconds):
        self._stop_image_autoplay()
        self.image_autoplay_duration = duration_seconds
        self.image_autoplay_start = time.time()
        self._image_timer.start(int(duration_seconds * 1000))

    def _stop_image_autoplay(self):
        if self._image_timer.isActive():
            self._image_timer.stop()
        self.image_autoplay_start = None
        self.image_autoplay_duration = 0

    def _on_image_timeout(self):
        if self.autoplay_enabled and self.is_current_image():
            self.play_next()

    # --- polling 500 ms ---

    def _poll(self):
        try:
            if self._overlay_tick:
                self._overlay_tick()
            if self.state.is_playing and not self.state.is_transitioning:
                state = self.engine.player.get_state()
                if state in (vlc.State.Ended, vlc.State.Stopped):
                    self.state.is_playing = False
                    if state == vlc.State.Ended and self.autoplay_enabled:
                        self.play_next()
                if not self.state.user_is_seeking:
                    self._emit_progress()
            elif not self.state.user_is_seeking:
                self.idle.emit()
        except Exception as exc:
            logging.error("Błąd w check_player_status:", exc_info=True)
            self._report_failure(exc)

    def _emit_progress(self):
        if self.is_current_image() and self.image_autoplay_start is not None:
            elapsed = time.time() - self.image_autoplay_start
            total = self.image_autoplay_duration
            fraction = min(1.0, elapsed / total) if total > 0 else 0.0
            self.progress_changed.emit(fraction, int(elapsed * 1000), int(total * 1000))
            return

        fraction = self.engine.player.get_position()
        if fraction < 0:
            fraction = -1.0
        elapsed = self.engine.player.get_time()
        total = self.engine.player.get_length()
        self.progress_changed.emit(fraction, elapsed, total)

    def _report_failure(self, exc):
        message = str(exc)
        self.failure.emit(message)
        if self._on_failure:
            self._on_failure(message)

    # --- zmiany wierszy playlisty ---

    def on_rows_inserted(self, _parent, first, last):
        count = last - first + 1
        self._set_playing_row(adjust_row_for_insert(self.state.playing_row, first, count))

    def on_rows_removed(self, _parent, first, last):
        count = last - first + 1
        had_playing_row = self.state.playing_row != -1
        self._set_playing_row(adjust_row_for_remove(self.state.playing_row, first, count))
        if had_playing_row and self.state.playing_row == -1:
            # Bez wiersza nie ma pozycji, do której należy dźwięk i obraz.
            self.playing_row_removed.emit()

    def on_rows_moved(self, _source_parent, source_start, source_end, _destination_parent, destination_child):
        count = source_end - source_start + 1
        self._set_playing_row(adjust_row_for_move(self.state.playing_row, source_start, count, destination_child))

    def on_model_reset(self):
        self._set_playing_row(-1)

    def _set_playing_row(self, row):
        if row != self.state.playing_row:
            self.state.playing_row = row
            self.playing_row_changed.emit(row)
