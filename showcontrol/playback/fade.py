"""Fade out: wygaszanie dźwięku i jasności przed zatrzymaniem. Bez UI."""

import logging

from PyQt6.QtCore import QObject, QTimer, pyqtSignal


class FadeController(QObject):
    """Stan przejścia fade i jego kroki.

    `finished` niesie `audio_only` oraz jasność startową, żeby wołający mógł
    zatrzymać odtwarzanie i przywrócić jasność po stopie. Sam nie zatrzymuje
    sesji — nie zna transportu.
    """

    finished = pyqtSignal(bool, float)

    def __init__(self, engine, set_brightness, parent=None):
        super().__init__(parent)
        self._engine = engine
        self._set_brightness = set_brightness
        self._state = None

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._step)

    @property
    def is_active(self):
        return self._state is not None

    def start(self, duration_seconds, start_brightness, audio_only):
        try:
            steps = max(5, int(duration_seconds * 10))
            has_audio = (self._engine.player.audio_get_track_count() > 0)
            self._state = {
                "step": 0,
                "steps": steps,
                "interval_ms": max(1, int((duration_seconds * 1000) / steps)),
                "has_audio": has_audio,
                "audio_only": audio_only,
                "start_vol": self._engine.player.audio_get_volume() if has_audio else 0,
                "start_bri": start_brightness,
            }
            self._timer.start(self._state["interval_ms"])
            return True
        except Exception:
            logging.error("Błąd podczas startu fade out:", exc_info=True)
            self._state = None
            return False

    def cancel(self):
        self._timer.stop()
        self._state = None

    def _step(self):
        state = self._state
        if not state:
            self._timer.stop()
            return

        state["step"] += 1
        progress = min(1.0, state["step"] / state["steps"])

        if state["has_audio"]:
            vol = state["start_vol"] * (1 - progress)
            self._engine.player.audio_set_volume(int(max(0, vol)))

        if not state["audio_only"]:
            bri = state["start_bri"] * (1 - progress)
            self._set_brightness(max(0.0, bri))

        if progress >= 1.0:
            self._timer.stop()
            self._state = None
            self.finished.emit(state["audio_only"], state["start_bri"])
