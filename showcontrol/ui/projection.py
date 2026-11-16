"""Widok projekcji i kurtyna przejścia."""

from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QApplication, QStackedLayout, QWidget

from showcontrol.bootstrap import set_window_icon

CURTAIN_FADE_IN_MS = 120
CURTAIN_FADE_OUT_MS = 300
CURTAIN_MIN_HOLD_MS = 120
CURTAIN_MAX_HOLD_MS = 800
CURTAIN_POLL_MS = 25


class OverlayViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.overlay_pixmap = None
        self.show_overlay = True
        self.opacity = 1.0
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        if self.show_overlay and self.overlay_pixmap and not self.overlay_pixmap.isNull():
            scaled = self.overlay_pixmap.scaled(
                w,
                h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            painter.setOpacity(self.opacity)
            painter.drawPixmap(int((w - scaled.width()) / 2), int((h - scaled.height()) / 2), scaled)


class ProjectionCurtain(QWidget):
    """Czarna kurtyna nad oknem projekcji."""

    def __init__(self, parent):
        super().__init__(
            parent,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setStyleSheet("background-color: black;")
        self.setWindowOpacity(0.0)

        self._apply_mode = None
        self._ready_check = None
        self._waited_ms = 0

        self._animation = QPropertyAnimation(self, b"windowOpacity", self)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._animation.finished.connect(self._on_animation_finished)

        self._ready_timer = QTimer(self)
        self._ready_timer.setInterval(CURTAIN_POLL_MS)
        self._ready_timer.timeout.connect(self._poll_ready)

    def play(self, apply_mode, ready_check=None):
        self._ready_timer.stop()
        self._animation.stop()
        self._apply_mode = apply_mode
        self._ready_check = ready_check
        self._waited_ms = 0
        self.setGeometry(self.parentWidget().frameGeometry())
        if not self.isVisible():
            self.setWindowOpacity(0.0)
            self.show()
        self.raise_()
        self._animate(1.0, CURTAIN_FADE_IN_MS)

    def cancel(self):
        self._ready_timer.stop()
        self._animation.stop()
        apply_mode, self._apply_mode = self._apply_mode, None
        self._ready_check = None
        if apply_mode is not None:
            apply_mode()
        self.hide()

    def follow(self):
        if self.isVisible():
            self.setGeometry(self.parentWidget().frameGeometry())

    def _animate(self, value, duration_ms):
        self._animation.stop()
        self._animation.setDuration(duration_ms)
        self._animation.setStartValue(self.windowOpacity())
        self._animation.setEndValue(value)
        self._animation.start()

    def _on_animation_finished(self):
        if self.windowOpacity() < 1.0:
            self.hide()
            return

        apply_mode, self._apply_mode = self._apply_mode, None
        if apply_mode is not None:
            apply_mode()

        if self._ready_check is None:
            self._fade_out()
        else:
            self._waited_ms = 0
            self._ready_timer.start()

    def _poll_ready(self):
        self._waited_ms += CURTAIN_POLL_MS
        ready = self._ready_check is None or self._ready_check()
        if ready and self._waited_ms >= CURTAIN_MIN_HOLD_MS:
            self._ready_timer.stop()
            self._fade_out()
        elif self._waited_ms >= CURTAIN_MAX_HOLD_MS:
            self._ready_timer.stop()
            self._fade_out()

    def _fade_out(self):
        self._animate(0.0, CURTAIN_FADE_OUT_MS)


class ProjectionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.Window)
        self.setWindowTitle("Projekcja - Odtwarzacz")
        self.setStyleSheet("background-color: black;")
        self.video_widget = QWidget()
        self.overlay_container = QWidget()
        self.overlay_stacked_layout = QStackedLayout(self.overlay_container)
        self.overlay_stacked_layout.setContentsMargins(0, 0, 0, 0)
        self.overlay_viewer = OverlayViewer()
        self.overlay_video_widget = QWidget()
        self.overlay_stacked_layout.addWidget(self.overlay_viewer)
        self.overlay_stacked_layout.addWidget(self.overlay_video_widget)
        self.stacked_layout = QStackedLayout(self)
        self.stacked_layout.addWidget(self.video_widget)
        self.stacked_layout.addWidget(self.overlay_container)
        self.set_mode_media()
        self.curtain = ProjectionCurtain(self)
        set_window_icon(self, "ikona_bw.ico")

    def set_mode_media(self):
        self.stacked_layout.setCurrentWidget(self.video_widget)

    def set_mode_overlay(self):
        self.stacked_layout.setCurrentWidget(self.overlay_container)

    def fade_to(self, apply_mode, ready_check=None):
        if not self.isVisible():
            apply_mode()
            return
        self.curtain.play(apply_mode, ready_check)

    def hideEvent(self, event):
        self.curtain.cancel()
        super().hideEvent(event)

    def moveEvent(self, event):
        if getattr(self, 'curtain', None):
            self.curtain.follow()
        super().moveEvent(event)

    def resizeEvent(self, event):
        if getattr(self, 'curtain', None):
            self.curtain.follow()
        super().resizeEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()

    def move_to_second_screen(self):
        screens = QApplication.screens()
        if len(screens) > 1:
            second_screen = screens[1]
            self.resize(800, 600)
            self.move(second_screen.geometry().topLeft() + second_screen.geometry().center() - self.rect().center())
            self.showFullScreen()
        else:
            self.resize(800, 600)

    def closeEvent(self, event):
        event.ignore()
        self.hide()
