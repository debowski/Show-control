"""Okno operatora i okno projekcji. Do faz 3 i 5 logika fade i UI są w tym pliku."""

import json
import os
import sys

from PyQt6.QtCore import (Qt, QTimer, QModelIndex, QPropertyAnimation,
                          QEasingCurve)
from PyQt6.QtGui import QShortcut, QKeySequence, QPainter
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QSlider, QListView,
                             QFileDialog, QMessageBox, QCheckBox, QStackedLayout,
                             QLabel, QGroupBox, QAbstractItemView, QSizePolicy,
                             QLineEdit, QSpinBox, QComboBox)

from showcontrol import __version__
from showcontrol.bootstrap import set_window_icon
from showcontrol.domain.media import is_audio_file
from showcontrol.domain.project_schema import (Project, ProjectItem,
                                                project_from_data, project_to_data)
from showcontrol.playback.engine import Engine
from showcontrol.playback.fade import FadeController
from showcontrol.playback.overlay import OverlayController
from showcontrol.playback.session import PlaybackSession
from showcontrol.ui.i18n import DEFAULT_LANGUAGE, get_t as translate
from showcontrol.ui.playlist_view import (PlaylistFilterProxyModel, PlaylistItemDelegate,
                                          PlaylistModel, PlaylistView)
from showcontrol.ui.theme import DEFAULT_THEME, THEME_KEYS, THEMES, generate_stylesheet

PROJECT_FILE_FILTER = "JSON (*.json)"
MEDIA_FILE_FILTER = "Media (*.mp4 *.mp3 *.mkv *.jpg *.png);;Wszystkie (*.*)"
EMPTY_TIME_LABEL = "00:00 / 00:00 (Pozostało: -00:00)"

KEYBOARD_SHORTCUTS = {
    "search": {"keys": [Qt.Key.Key_F3]},
    "focus_playlist": {"keys": [Qt.Key.Key_F2]},
    "play": {
        "keys": [Qt.Key.Key_F4],
        "playlist_keys": [Qt.Key.Key_Return, Qt.Key.Key_Enter],
    },
    "pause": {"keys": [Qt.Key.Key_Space]},
    "stop": {"keys": [Qt.Key.Key_F5]},
    "remove": {"keys": [Qt.Key.Key_Delete]},
    "save_project": {"keys": [Qt.Key.Key_F12]},
    "fade_out": {"keys": [Qt.Key.Key_F1]},
    "fullscreen": {"keys": [Qt.Key.Key_F11]},
    "overlay_on_audio": {"keys": [Qt.Key.Key_F10]},
    "force_overlay": {"keys": [Qt.Key.Key_F9]},
    "previous": {
        "keys": [Qt.Key.Key_F6],
        "navigation": {
            "remote": Qt.Key.Key_Left,
            "standard": Qt.Key.Key_Up,
        },
    },
    "next": {
        "keys": [Qt.Key.Key_F7],
        "navigation": {
            "remote": Qt.Key.Key_Right,
            "standard": Qt.Key.Key_Down,
        },
    },
}

KEY_LABELS = {
    Qt.Key.Key_Delete: "Del",
    Qt.Key.Key_Down: "↓",
    Qt.Key.Key_Enter: "Enter",
    Qt.Key.Key_Left: "←",
    Qt.Key.Key_Return: "Enter",
    Qt.Key.Key_Right: "→",
    Qt.Key.Key_Space: "Spacja",
    Qt.Key.Key_Up: "↑",
}

KEY_TOOLTIP_LABELS = {
    Qt.Key.Key_Delete: "Delete",
    Qt.Key.Key_Down: "Strzałka w dół",
    Qt.Key.Key_Left: "Strzałka w lewo",
    Qt.Key.Key_Right: "Strzałka w prawo",
    Qt.Key.Key_Up: "Strzałka w górę",
}


def key_label(key, tooltip=False):
    labels = KEY_TOOLTIP_LABELS if tooltip else KEY_LABELS
    return labels.get(key, QKeySequence(key).toString(QKeySequence.SequenceFormat.NativeText))


def shortcut_label(name, groups=("keys",), extra_keys=None, separator="/", tooltip=False):
    keys = []
    for group in groups:
        keys.extend(KEYBOARD_SHORTCUTS[name].get(group, []))
    if extra_keys:
        keys.extend(extra_keys)

    labels = []
    for key in keys:
        label = key_label(key, tooltip)
        if label and label not in labels:
            labels.append(label)
    return separator.join(labels)


def navigation_shortcut(name, remote_enabled):
    mode = "remote" if remote_enabled else "standard"
    return KEYBOARD_SHORTCUTS[name]["navigation"][mode]

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
            scaled = self.overlay_pixmap.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            painter.setOpacity(self.opacity)
            painter.drawPixmap(int((w - scaled.width())/2), int((h - scaled.height())/2), scaled)

CURTAIN_FADE_IN_MS = 120
CURTAIN_FADE_OUT_MS = 300
CURTAIN_MIN_HOLD_MS = 120
CURTAIN_MAX_HOLD_MS = 800
CURTAIN_POLL_MS = 25


class ProjectionCurtain(QWidget):
    """Czarna kurtyna nad oknem projekcji — przejście media ↔ overlay.

    VLC rysuje obraz w natywnym oknie potomnym, więc zwykły widget w oknie
    projekcji schowałby się pod wideo. Kurtyna jest osobnym oknem top-level:
    zasłania natywny obraz, pozwala przełączyć tryb w czerni i płynnie odsłonić
    nowy obraz. `ready_check` opóźnia odsłonięcie, aż overlay ma pierwszy
    obraz — dzięki temu nie ma czarnej dziury przed startem wideo.
    """

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
        # Przerwane przejście wznawia się od bieżącej krycia, nie od zera —
        # szybkie F9 nie miga czernią wstecz.
        self._animate(1.0, CURTAIN_FADE_IN_MS)

    def cancel(self):
        self._ready_timer.stop()
        self._animation.stop()
        apply_mode, self._apply_mode = self._apply_mode, None
        self._ready_check = None
        # Przełączenie nie może zginąć, jeśli okno zniknie w trakcie przejścia.
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
        """Przełącza tryb projekcji przez kurtynę.

        Gdy okno projekcji jest ukryte, nie ma czego zasłaniać — przełączenie
        idzie od razu.
        """
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
        # Zamiast całkowicie kasować okno podglądu przy "X", po prostu je chowamy.
        # Zapobiega to utracie HWND.
        event.ignore()
        self.hide()

class App(QMainWindow):
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
        self.session.start()
        
        last_project = self.settings.value("last_project", "")
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
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # --- GÓRNY PASEK ZARZĄDZANIA ---
        top_bar = QHBoxLayout()
        mgmt_left = QHBoxLayout()
        self.add_btn = QPushButton("✚ Dodaj pliki")
        self.add_btn.setToolTip("Dodaj nowe pliki do listy")
        self.add_btn.clicked.connect(self.add_files)
        self.remove_btn = QPushButton()
        self.remove_btn.clicked.connect(self.remove_file)
        mgmt_left.addWidget(self.add_btn)
        mgmt_left.addWidget(self.remove_btn)
        
        mgmt_right = QHBoxLayout()
        self.load_proj_btn = QPushButton("📂 Wczytaj Projekt")
        self.load_proj_btn.setToolTip("Wczytaj zapisaną listę plików")
        self.load_proj_btn.clicked.connect(self.load_project)
        self.save_proj_btn = QPushButton()
        self.save_proj_btn.clicked.connect(self.save_project)
        mgmt_right.addWidget(self.load_proj_btn)
        mgmt_right.addWidget(self.save_proj_btn)
        
        top_bar.addLayout(mgmt_left)
        top_bar.addStretch()
        
        self.overlay_btn = QPushButton("📁 Wybierz plik nakładki")
        self.overlay_btn.setToolTip("Wybierz obrazek lub grafikę do wyświetlania")
        self.overlay_btn.clicked.connect(self.select_overlay)
        
        self.window_btn = QPushButton("👁 Ukryj Okno")
        self.window_btn.setObjectName("HideBtn")
        self.window_btn.setToolTip("Ukryj lub pokaż okno projekcji")
        self.window_btn.clicked.connect(self.toggle_projection_window)
        
        mgmt_center = QHBoxLayout()
        mgmt_center.addWidget(self.overlay_btn)
        mgmt_center.addWidget(self.window_btn)
        top_bar.addLayout(mgmt_center)
        
        top_bar.addStretch()
        top_bar.addLayout(mgmt_right)
        layout.addLayout(top_bar)

        # --- PASEK WYSZUKIWANIA ---
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.filter_playlist)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # --- LISTA PLIKÓW ---
        self.proxy_model = PlaylistFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.playlist_model)
        # Na żywo aktualizuj tryb projekcji gdy operator zmieni checkbox nakładki
        self.playlist_model.dataChanged.connect(self._on_playlist_overlay_changed)
        
        self.playlist = PlaylistView(self)
        self.playlist.setModel(self.proxy_model)
        self.playlist.setItemDelegate(PlaylistItemDelegate(self.playlist))
        self.playlist.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.playlist.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.playlist.setAlternatingRowColors(True)
        self.playlist.viewport().setMouseTracking(True)
        
        # Konfiguracja Drag & Drop
        # DragDrop (nie InternalMove) pozwala akceptować pliki z zewnątrz (Eksplorator)
        self.playlist.setDragEnabled(True)
        self.playlist.setAcceptDrops(True)
        self.playlist.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.playlist.setDropIndicatorShown(True)
        self.playlist.setDefaultDropAction(Qt.DropAction.MoveAction)
        
        self.playlist.doubleClicked.connect(lambda idx: self.play_media())

        # --- PRZYCISKI PRZESUWANIA KOLEJNOŚCI ---
        self.move_up_btn = QPushButton("▲")
        self.move_up_btn.setObjectName("MoveBtn")
        self.move_up_btn.setToolTip("Przesuń plik w górę")
        self.move_up_btn.setFixedSize(28, 28)
        self.move_up_btn.clicked.connect(self.move_item_up)

        self.move_down_btn = QPushButton("▼")
        self.move_down_btn.setObjectName("MoveBtn")
        self.move_down_btn.setToolTip("Przesuń plik w dół")
        self.move_down_btn.setFixedSize(28, 28)
        self.move_down_btn.clicked.connect(self.move_item_down)

        move_btn_layout = QVBoxLayout()
        move_btn_layout.setContentsMargins(0, 0, 0, 0)
        move_btn_layout.setSpacing(4)
        move_btn_layout.addWidget(self.move_up_btn)
        move_btn_layout.addWidget(self.move_down_btn)
        move_btn_layout.addStretch()

        playlist_row = QHBoxLayout()
        playlist_row.setSpacing(6)
        playlist_row.addWidget(self.playlist, stretch=1)
        playlist_row.addLayout(move_btn_layout)
        layout.addLayout(playlist_row, stretch=1)

        # --- SEKCJA TRANSPORTU ---
        transport_frame = QGroupBox("Kontrola odtwarzania")
        trans_layout = QVBoxLayout(transport_frame)
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.setFixedHeight(25)
        self.progress_slider.sliderMoved.connect(self.session.set_position)
        self.progress_slider.sliderPressed.connect(self.session.begin_seek)
        self.progress_slider.sliderReleased.connect(
            lambda: self.session.end_seek(self.progress_slider.value())
        )
        
        self.time_label = QLabel(EMPTY_TIME_LABEL)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setObjectName("TimeLabel")

        trans_layout.addWidget(self.progress_slider)
        trans_layout.addWidget(self.time_label)
        
        btns_grid = QHBoxLayout()
        btns_grid.setSpacing(5)
        self.prev_btn = QPushButton()
        self.prev_btn.setObjectName("TransportBtn")
        self.prev_btn.clicked.connect(self.play_previous_file)
        
        self.play_btn = QPushButton()
        self.play_btn.setObjectName("PlayBtn")
        self.play_btn.clicked.connect(self.play_media)
        
        self.pause_btn = QPushButton()
        self.pause_btn.setObjectName("TransportBtn")
        self.pause_btn.clicked.connect(self.toggle_play_pause)
        
        self.stop_btn = QPushButton()
        self.stop_btn.setObjectName("StopBtn")
        self.stop_btn.clicked.connect(self.stop_media)
        
        self.next_btn = QPushButton()
        self.next_btn.setObjectName("TransportBtn")
        self.next_btn.clicked.connect(self.play_next_file)
        
        for btn in [self.prev_btn, self.play_btn, self.pause_btn, self.stop_btn, self.next_btn]:
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            btns_grid.addWidget(btn)
        trans_layout.addLayout(btns_grid)
        layout.addWidget(transport_frame)

        # --- DOLNY PANEL ---
        bottom_panel = QHBoxLayout()
        view_group = QGroupBox("Widok i Efekty")
        view_layout = QVBoxLayout(view_group)
        self.fade_btn = QPushButton()
        self.fade_btn.setObjectName("FadeBtn")
        self.fade_btn.clicked.connect(self.fade_out)
        self.fullscreen_btn = QPushButton()
        self.fullscreen_btn.clicked.connect(self.toggle_projection_fullscreen)
        self.force_overlay_btn = QPushButton()
        self.force_overlay_btn.setCheckable(True)
        self.force_overlay_btn.setObjectName("TransportBtn")
        self.force_overlay_btn.setToolTip("Pokaż overlay zamiast wideo na wyjściu projekcji")
        self.force_overlay_btn.toggled.connect(self.toggle_overlay)
        view_layout.addWidget(self.fade_btn)
        view_layout.addWidget(self.fullscreen_btn)
        view_layout.addWidget(self.force_overlay_btn)
        
        audio_group = QGroupBox("Sterowanie")
        audio_main_layout = QHBoxLayout(audio_group)
        
        # --- Suwak głośności ---
        vol_slider_layout = QVBoxLayout()
        vol_title = QLabel("🔊 Głośność")
        vol_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vol_title.setStyleSheet("font-size: 8pt; color: #aaaaaa;")
        self.vol_label = QLabel("100%")
        self.vol_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.volume_slider = QSlider(Qt.Orientation.Vertical)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        vol_slider_layout.addWidget(vol_title)
        vol_slider_layout.addWidget(self.vol_label)
        vol_slider_layout.addWidget(self.volume_slider, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        # --- Suwak prędkości fade ---
        fade_slider_layout = QVBoxLayout()
        fade_title = QLabel("⏱ Fade")
        fade_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fade_title.setStyleSheet("font-size: 8pt; color: #aaaaaa;")
        self.fade_speed_label = QLabel("0.8s")
        self.fade_speed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fade_speed_slider = QSlider(Qt.Orientation.Vertical)
        # Zakres 0–10 (= 0.0s–1.0s, skalujemy /10 → czyli 10 = 1.0s)
        self.fade_speed_slider.setRange(0, 10)
        self.fade_speed_slider.setToolTip("Czas trwania efektu fade (0.0s – 1.0s)")
        # Podłączamy przed setValue, żeby etykieta od razu pokazała wartość domyślną
        self.fade_speed_slider.valueChanged.connect(self._on_fade_speed_changed)
        self.fade_speed_slider.setValue(8)   # domyślnie 0.8s
        fade_slider_layout.addWidget(fade_title)
        fade_slider_layout.addWidget(self.fade_speed_label)
        fade_slider_layout.addWidget(self.fade_speed_slider, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        # --- Suwak jasności ---
        bri_slider_layout = QVBoxLayout()
        bri_title = QLabel("💡 Jasność")
        bri_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bri_title.setStyleSheet("font-size: 8pt; color: #aaaaaa;")
        self.bri_label = QLabel("100%")
        self.bri_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.brightness_slider = QSlider(Qt.Orientation.Vertical)
        self.brightness_slider.setRange(0, 100)
        self.brightness_slider.setValue(100)
        self.brightness_slider.setToolTip("Jasność okna projekcji (0% – 100%)")
        self.brightness_slider.valueChanged.connect(self.set_brightness)
        bri_slider_layout.addWidget(bri_title)
        bri_slider_layout.addWidget(self.bri_label)
        bri_slider_layout.addWidget(self.brightness_slider, alignment=Qt.AlignmentFlag.AlignHCenter)

        audio_main_layout.addStretch()
        audio_main_layout.addLayout(vol_slider_layout)
        audio_main_layout.addSpacing(12)
        audio_main_layout.addLayout(bri_slider_layout)
        audio_main_layout.addSpacing(12)
        audio_main_layout.addLayout(fade_slider_layout)
        audio_main_layout.addSpacing(12)

        audio_main_layout.addStretch()
        
        settings_group = QGroupBox("Ustawienia")
        set_layout = QVBoxLayout(settings_group)
        # Language selector will be added here; default set from settings
        self.language = self.settings.value("language", DEFAULT_LANGUAGE)

        self.autoplay_checkbox = QCheckBox()
        # we'll set texts after building UI via apply_translations()
        self.autoplay_checkbox.stateChanged.connect(self._on_autoplay_changed)

        image_speed_layout = QHBoxLayout()
        image_speed_title = QLabel("⏱ Prędkość grafiki")
        self.image_switch_delay = QSpinBox()
        self.image_switch_delay.setRange(1, 60)
        self.image_switch_delay.setValue(5)
        self.image_switch_delay.setSuffix(" s")
        self.image_switch_delay.setToolTip("Czas wyświetlania plików graficznych w sekundach przy autoodtwarzaniu")
        self.image_switch_delay.setFixedWidth(100)
        image_speed_layout.addWidget(image_speed_title)
        image_speed_layout.addStretch()
        image_speed_layout.addWidget(self.image_switch_delay)

        self.remote_checkbox = QCheckBox("Tryb Pilota (L/P)")
        self.remote_checkbox.setChecked(True)
        self.remote_checkbox.stateChanged.connect(lambda: self.update_shortcuts())
        self.overlay_on_audio_checkbox = QCheckBox()
        self.overlay_on_audio_checkbox.setChecked(False)
        self.overlay_on_audio_checkbox.stateChanged.connect(lambda: self.update_overlay_visibility())

        # --- Theme selector ---
        theme_row = QHBoxLayout()
        self.theme_label = QLabel()
        self.theme_combo = QComboBox()
        for key in THEME_KEYS:
            self.theme_combo.addItem(THEMES[key]["name"], key)
        saved_theme = self.settings.value("theme", DEFAULT_THEME)
        saved_idx = THEME_KEYS.index(saved_theme) if saved_theme in THEME_KEYS else 0
        self.theme_combo.setCurrentIndex(saved_idx)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        theme_row.addWidget(self.theme_label)
        theme_row.addWidget(self.theme_combo, stretch=1)

        set_layout.addWidget(self.autoplay_checkbox)
        set_layout.addLayout(image_speed_layout)
        set_layout.addWidget(self.remote_checkbox)
        set_layout.addWidget(self.overlay_on_audio_checkbox)
        set_layout.addLayout(theme_row)
        # --- Language selector ---
        lang_row = QHBoxLayout()
        self.lang_label = QLabel()
        self.lang_combo = QComboBox()
        # add languages by key and display name
        self.lang_combo.addItem("Polski", "pl")
        self.lang_combo.addItem("English", "en")
        # set current
        idx = 0 if self.language == "pl" else 1
        self.lang_combo.setCurrentIndex(idx)
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        lang_row.addWidget(self.lang_label)
        lang_row.addWidget(self.lang_combo, stretch=1)
        set_layout.addLayout(lang_row)
        set_layout.addStretch()
        
        bottom_panel.addWidget(view_group, stretch=1)
        bottom_panel.addWidget(audio_group, stretch=1)
        bottom_panel.addWidget(settings_group, stretch=1)
        layout.addLayout(bottom_panel)

        self.setup_button_feedback(
            self.add_btn, self.remove_btn, self.load_proj_btn, self.save_proj_btn,
            self.overlay_btn, self.window_btn, self.prev_btn, self.play_btn,
            self.pause_btn, self.stop_btn, self.next_btn, self.fade_btn,
            self.fullscreen_btn, self.force_overlay_btn,
        )
        self.update_shortcut_descriptions()
        self.init_shortcuts()
        # Apply translations at the end of UI init so all widgets exist
        self.apply_translations()

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
        # Projection window title
        self.projection_window.setWindowTitle(self.get_t('projection_window_title'))

        # Top bar
        self.add_btn.setText(self.get_t('add_files'))
        self.add_btn.setToolTip(self.get_t('add_files_tooltip'))
        self.load_proj_btn.setText(self.get_t('load_project'))
        self.load_proj_btn.setToolTip(self.get_t('load_project_tooltip'))
        self.save_proj_btn.setText(self.get_t('save_project'))
        self.save_proj_btn.setToolTip(self.get_t('save_project_tooltip'))
        self.overlay_btn.setText(self.get_t('select_overlay'))
        self.overlay_btn.setToolTip(self.get_t('select_overlay_tooltip'))
        self.window_btn.setText(self.get_t('toggle_projection'))
        self.window_btn.setToolTip(self.get_t('toggle_projection_tooltip'))

        # Search
        self.search_input.setPlaceholderText(self.get_t('search_placeholder'))

        # Update QGroupBox titles (match known Polish/English originals defensively)
        for gb in self.findChildren(QGroupBox):
            t = gb.title()
            if t in ("Kontrola odtwarzania", "Playback Control", ""):
                gb.setTitle(self.get_t('playback_control'))
            elif t in ("Widok i Efekty", "View & Effects", ""):
                gb.setTitle(self.get_t('view_effects'))
            elif t in ("Sterowanie", "Control", ""):
                gb.setTitle(self.get_t('control'))
            elif t in ("Ustawienia", "Settings", ""):
                gb.setTitle(self.get_t('settings'))

        # Update QLabel texts for small labels (volume, fade, brightness, image speed, theme, language)
        for lbl in self.findChildren(QLabel):
            txt = lbl.text()
            if "Głośność" in txt or "Volume" in txt:
                lbl.setText(self.get_t('volume'))
            elif "Jasność" in txt or "Brightness" in txt:
                lbl.setText(self.get_t('brightness'))
            elif "Prędkość grafiki" in txt or "Image Speed" in txt:
                lbl.setText(self.get_t('image_speed'))
            elif "Fade" in txt and ("⏱" in txt or "Fade" in txt):
                lbl.setText(self.get_t('fade'))
            elif txt.strip() in ("🎨 Motyw", "🎨 Theme"):
                lbl.setText(self.get_t('theme'))
            # language label: original was empty — if detected placeholder, set 'Language' under settings
            elif txt.strip() in ("", "Ustawienia", "Settings"):
                # careful: avoid overwriting groupbox titles; only set if label appears in settings layout
                parent = lbl.parent()
                settings_group_in = False
                if parent:
                    settings_group_in = any(isinstance(w, QGroupBox) and w.title() == self.get_t('settings') for w in parent.findChildren(QGroupBox))
                if settings_group_in:
                    lbl.setText(self.get_t('settings'))

        # Settings group labels
        # autoplay checkbox
        self.autoplay_checkbox.setText(self.get_t('autoplay'))
        # remote checkbox
        self.remote_checkbox.setText(self.get_t('remote_mode'))
        # overlay on audio checkbox
        self.overlay_on_audio_checkbox.setText(self.get_t('overlay_on_audio'))
        # theme label: set via translations
        try:
            self.theme_label.setText(self.get_t('theme'))
        except Exception:
            pass

        # language row
        try:
            # set language label text
            self.lang_label.setText(self.get_t('language'))
        except Exception:
            pass

        # Update some button short texts that depend on shortcuts
        self.update_shortcut_descriptions()

    def _on_language_changed(self, index):
        key = self.lang_combo.currentData()
        if not key:
            return
        self.language = key
        self.settings.setValue('language', key)
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
        remote_enabled = self.remote_checkbox.isChecked()
        prev_shortcut = navigation_shortcut("previous", remote_enabled)
        next_shortcut = navigation_shortcut("next", remote_enabled)

        self.remove_btn.setText(f"{self.get_t('remove_short')} ({shortcut_label('remove')})")
        self.remove_btn.setToolTip(f"{self.get_t('remove_short')} ({shortcut_label('remove', tooltip=True)})")
        self.save_proj_btn.setText(f"{self.get_t('save_project')} ({shortcut_label('save_project')})")
        self.save_proj_btn.setToolTip(f"{self.get_t('save_project_tooltip')} ({shortcut_label('save_project')})")
        self.search_input.setPlaceholderText(f"{self.get_t('search_placeholder')} ({shortcut_label('search')})")

        self.prev_btn.setText(f"{self.get_t('previous_short')} ({shortcut_label('previous', extra_keys=[prev_shortcut])})")
        self.prev_btn.setToolTip(f"{self.get_t('previous_short')} ({shortcut_label('previous', extra_keys=[prev_shortcut], separator=' / ', tooltip=True)})")
        self.play_btn.setText(f"{self.get_t('play_short')} ({shortcut_label('play', groups=('keys', 'playlist_keys'))})")
        self.play_btn.setToolTip(f"{self.get_t('play_short')} ({shortcut_label('play')})")
        self.pause_btn.setText(f"{self.get_t('pause_short')} ({shortcut_label('pause')})")
        self.pause_btn.setToolTip(f"{self.get_t('pause_short')} ({shortcut_label('pause')})")
        self.stop_btn.setText(f"{self.get_t('stop_short')} ({shortcut_label('stop')})")
        self.stop_btn.setToolTip(f"{self.get_t('stop_short')} ({shortcut_label('stop')})")
        self.next_btn.setText(f"{self.get_t('next_short')} ({shortcut_label('next', extra_keys=[next_shortcut])})")
        self.next_btn.setToolTip(f"{self.get_t('next_short')} ({shortcut_label('next', extra_keys=[next_shortcut], separator=' / ', tooltip=True)})")

        self.fade_btn.setText(f"{self.get_t('fade_out')} ({shortcut_label('fade_out')})")
        self.fade_btn.setToolTip(f"{self.get_t('fade_out')} ({shortcut_label('fade_out')})")
        self.fullscreen_btn.setText(f"{self.get_t('fullscreen')} ({shortcut_label('fullscreen')})")
        self.fullscreen_btn.setToolTip(f"{self.get_t('fullscreen')} ({shortcut_label('fullscreen')})")
        self.overlay_on_audio_checkbox.setText(f"{self.get_t('overlay_on_audio')} ({shortcut_label('overlay_on_audio')})")
        self.force_overlay_btn.setText(f"{self.get_t('force_overlay')} ({shortcut_label('force_overlay')})")
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

    def _on_progress(self, fraction, elapsed_ms, total_ms):
        if fraction >= 0:
            self.progress_slider.setValue(int(fraction * 1000))
        if elapsed_ms >= 0 and total_ms >= 0:
            rem = max(0, total_ms - elapsed_ms)
            self.time_label.setText(
                f"{self.format_time(elapsed_ms)} / {self.format_time(total_ms)}"
                f" (Pozostało: -{self.format_time(rem)})"
            )

            # Zabezpieczenie (self-healing): przesyłamy głośność z suwaka przez
            # pierwsze 2 sekundy, co gwarantuje, że VLC poprawnie to odbierze
            if elapsed_ms < 2000:
                self.engine.player.audio_set_volume(self.volume_slider.value())

    def _on_idle(self):
        self.progress_slider.setValue(0)
        self.time_label.setText(EMPTY_TIME_LABEL)

    def _on_stopping(self, keep_overlay):
        if not keep_overlay:
            self._set_projection_brightness(0.0)

    def _on_transition_finished(self):
        self._set_projection_brightness(self.brightness_slider.value() / 100.0)

    def add_files(self):
        title = self.get_t('add_media_dialog')
        files, _ = QFileDialog.getOpenFileNames(self, title, "", MEDIA_FILE_FILTER)
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
        filter_str = self.get_t('select_overlay_dialog') + " (*.png *.jpg *.jpeg *.bmp *.gif *.mp4 *.mkv);;" + self.get_t('select_overlay_dialog') + " (*.png *.jpg *.jpeg *.bmp *.gif);;" + self.get_t('select_overlay_dialog') + " (*.mp4 *.mkv);;Wszystkie (*.*)"
        path, _ = QFileDialog.getOpenFileName(self, self.get_t('select_overlay_dialog'), "", filter_str)
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
        path, _ = QFileDialog.getSaveFileName(self, self.get_t('save_dialog'), "", PROJECT_FILE_FILTER)
        if path:
            try:
                project = Project(
                    items=tuple(
                        ProjectItem(entry.path, entry.overlay, entry.overlay_path)
                        for entry in self.playlist_model.entries()
                    ),
                    overlay_path=self.overlay.global_asset,
                )
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(project_to_data(project), f, ensure_ascii=False, indent=4)
                self.settings.setValue("last_project", path)
                self.update_window_title(path)
            except Exception as e:
                QMessageBox.critical(self, self.get_t('save_error_title'), f"Nie udało się zapisać projektu:\n{e}")

    def load_project(self):
        path, _ = QFileDialog.getOpenFileName(self, self.get_t('load_dialog'), "", PROJECT_FILE_FILTER)
        if path:
            self._load_project_file(path)
            
    def _load_project_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            project = project_from_data(data)
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
                    print(f"Pominięto brakujący plik podczas wczytywania: {item.path}")

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

            self.settings.setValue("last_project", path)
            self.update_window_title(path)
        except Exception as e:
            QMessageBox.critical(self, self.get_t('load_error_title'), f"Nie udało się wczytać projektu:\n{e}")

    def _on_theme_changed(self, _index):
        key = self.theme_combo.currentData()
        self.change_theme(key)

    def change_theme(self, theme_key: str):
        """Apply a new theme to the application and persist the choice."""
        if theme_key not in THEMES:
            theme_key = DEFAULT_THEME
        QApplication.instance().setStyleSheet(generate_stylesheet(theme_key))
        self.settings.setValue("theme", theme_key)

    def closeEvent(self, event):
        self.projection_window.close()
        super().closeEvent(event)
