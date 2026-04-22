# Show-control Version 2.0
# Copyright (C) 2026 Piotr Dębowski
#
# Professional Broadcast Edition

import sys
import os
import time
import threading
import json
import random
import math

try:
    import vlc
except ImportError:
    print("Błąd: Biblioteka python-vlc nie jest zainstalowana.")
    print("Zainstaluj ją używając: pip install python-vlc")
    sys.exit(1)

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QSlider, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QFileDialog, 
                             QMessageBox, QCheckBox, QStackedLayout, QLabel, 
                             QFrame, QGroupBox, QAbstractItemView, QSizePolicy,
                             QLineEdit)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QShortcut, QKeySequence, QPainter, QColor, QPixmap, QFont

# --- STAŁE KOLORYSTYCZNE I STYLIZACJA ---
COLOR_BG_MAIN = "#1e1e1e"
COLOR_BG_DARK = "#252526"
COLOR_ACCENT = "#007acc"
COLOR_PLAY = "#2d8a49"
COLOR_STOP = "#a1260d"
COLOR_FADE = "#d18616"
COLOR_HIDE = "#4a4a4a"
COLOR_TEXT = "#d4d4d4"
COLOR_TEXT_DIM = "#aaaaaa"
COLOR_BORDER = "#3c3c3c"

APP_STYLESHEET = f"""
    QMainWindow, QWidget {{
        background-color: {COLOR_BG_MAIN};
        color: {COLOR_TEXT};
        font-family: 'Segoe UI', system-ui;
        font-size: 10pt;
    }}
    
    QGroupBox {{
        border: 1px solid {COLOR_BORDER};
        border-radius: 4px;
        margin-top: 1.2em;
        font-weight: bold;
        color: {COLOR_ACCENT};
        padding: 10px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
    }}
    
    /* Przyciski */
    QPushButton {{
        background-color: #333333;
        border: 1px solid {COLOR_BORDER};
        padding: 8px 15px;
        border-radius: 3px;
        min-height: 22px;
    }}
    QPushButton:hover {{ background-color: #3e3e42; }}
    QPushButton:pressed {{ background-color: {COLOR_ACCENT}; }}
    QPushButton:checked {{ 
        background-color: {COLOR_ACCENT}; 
        color: white; 
        font-weight: bold; 
        border: 1px solid #005a9e; 
    }}
    
    QPushButton#PlayBtn {{ 
        background-color: {COLOR_PLAY}; 
        color: white;
        font-weight: bold; 
        font-size: 11pt;
        min-height: 45px;
    }}
    QPushButton#PlayBtn:hover {{ background-color: #3aa659; }}
    
    QPushButton#StopBtn {{ 
        background-color: {COLOR_STOP}; 
        color: white;
        font-weight: bold;
        font-size: 11pt;
        min-height: 45px;
    }}
    QPushButton#StopBtn:hover {{ background-color: #be2d10; }}
    
    QPushButton#TransportBtn {{
        font-weight: bold;
        min-height: 45px;
    }}

    QPushButton#FadeBtn {{ background-color: {COLOR_FADE}; color: white; }}
    QPushButton#FadeBtn:hover {{ background-color: #e5951a; }}
    
    QPushButton#HideBtn {{ background-color: {COLOR_HIDE}; color: #cccccc; }}
    
    /* Tabela */
    QTableWidget {{
        background-color: {COLOR_BG_DARK};
        border: 1px solid {COLOR_BORDER};
        gridline-color: #2d2d2d;
        outline: none;
    }}
    QHeaderView::section {{
        background-color: #333333;
        color: {COLOR_TEXT_DIM};
        padding: 5px;
        border: 1px solid {COLOR_BORDER};
    }}
    QTableWidget::item {{
        padding: 5px;
    }}
    QTableWidget::item:selected {{
        background-color: {COLOR_ACCENT};
        color: white;
    }}
    
    /* Suwaki i Pola Tekstowe */
    QLineEdit {{
        background-color: {COLOR_BG_DARK};
        border: 1px solid {COLOR_BORDER};
        color: {COLOR_TEXT};
        padding: 5px;
        border-radius: 3px;
    }}
    
    QSlider::groove:horizontal {{
        border: 1px solid {COLOR_BORDER};
        height: 8px;
        background: {COLOR_BG_DARK};
        border-radius: 4px;
    }}
    QSlider::handle:horizontal {{
        background: {COLOR_ACCENT};
        width: 18px;
        height: 18px;
        margin: -6px 0;
        border-radius: 9px;
    }}
    
    QSlider::groove:vertical {{
        border: 1px solid {COLOR_BORDER};
        width: 8px;
        background: {COLOR_BG_DARK};
        border-radius: 4px;
    }}
    QSlider::handle:vertical {{
        background: {COLOR_ACCENT};
        width: 18px;
        height: 18px;
        margin: 0 -6px;
        border-radius: 9px;
    }}
"""

class AudioVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bars = 30
        self.logo_pixmap = None
        self.show_logo = True
        self.heights = [0 for _ in range(self.bars)]
        self.targets = [0 for _ in range(self.bars)]
        self.is_active = False
        self.volume_multiplier = 1.0
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_bars)
        
    def start(self):
        self.is_active = True
        self.timer.start(50)
        self.show()
        
    def stop(self):
        self.is_active = False
        self.timer.stop()
        self.update()
        self.hide()
        
    def update_bars(self):
        if not self.is_active: return
        for i in range(self.bars):
            if random.random() < 0.2:
                center_factor = math.sin((i / (self.bars - 1)) * math.pi)
                self.targets[i] = (random.random()**2 * 100 * center_factor + 10) * self.volume_multiplier
            else:
                self.targets[i] *= 0.8
            self.heights[i] += (self.targets[i] - self.heights[i]) * 0.4
        self.update()

    def paintEvent(self, event):
        if not self.is_active: return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        if self.show_logo and self.logo_pixmap and not self.logo_pixmap.isNull():
            scaled = self.logo_pixmap.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            painter.drawPixmap(int((w - scaled.width())/2), int((h - scaled.height())/2), scaled)

class VideoDisplay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_widget = QWidget()
        self.vis_container = QWidget()
        vis_layout = QVBoxLayout(self.vis_container)
        vis_layout.setContentsMargins(0, 0, 0, 0)
        self.visualizer = AudioVisualizer()
        vis_layout.addWidget(self.visualizer)
        self.stacked_layout = QStackedLayout(self)
        self.stacked_layout.addWidget(self.video_widget)
        self.stacked_layout.addWidget(self.vis_container)
        self.set_mode_video()

    def set_mode_video(self):
        self.stacked_layout.setCurrentWidget(self.video_widget)
        self.visualizer.stop()
        
    def set_mode_audio(self):
        self.stacked_layout.setCurrentWidget(self.vis_container)
        self.visualizer.start()

class ProjectionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.Window)
        self.setWindowTitle("Projekcja - Odtwarzacz")
        self.setStyleSheet("background-color: black;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.display = VideoDisplay()
        layout.addWidget(self.display)
        
        # Aliasy dla kompatybilności wstecznej
        self.video_widget = self.display.video_widget
        self.visualizer = self.display.visualizer

    def set_mode_video(self):
        self.display.set_mode_video()
        
    def set_mode_audio(self):
        self.display.set_mode_audio()
        
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.isFullScreen(): self.showNormal()
            else: self.showFullScreen()

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

class PlaylistTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["Nazwa pliku", "Czas"])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(1, 100)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)
        
        # Konfiguracja Drag & Drop
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        
        self.playing_row = -1

    def add_file(self, file_path, vlc_instance):
        filename = os.path.basename(file_path)
        row = self.rowCount()
        self.insertRow(row)
        
        name_item = QTableWidgetItem(filename)
        name_item.setData(Qt.ItemDataRole.UserRole, file_path)
        name_item.setToolTip(file_path)
        self.setItem(row, 0, name_item)
        
        time_item = QTableWidgetItem("--:--")
        time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(row, 1, time_item)
        
        threading.Thread(target=self._update_duration, args=(file_path, row, vlc_instance), daemon=True).start()

    def _update_duration(self, path, row, vlc_instance):
        media = vlc_instance.media_new(path)
        media.parse_with_options(vlc.MediaParseFlag.local, 0)
        for _ in range(10):
            if media.get_parsed_status() == vlc.MediaParsedStatus.done: break
            time.sleep(0.1)
        
        ms = media.get_duration()
        if ms > 0:
            s, _ = divmod(ms, 1000)
            m, s = divmod(s, 60)
            h, m = divmod(m, 60)
            time_str = f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
            if row < self.rowCount():
                item = self.item(row, 1)
                if item: item.setText(time_str)

    def set_playing_row(self, row):
        # Wyczyść poprzednie podświetlenie
        if self.playing_row != -1 and self.playing_row < self.rowCount():
            for c in range(2):
                it = self.item(self.playing_row, c)
                if it:
                    it.setBackground(QColor("transparent"))
                    it.setFont(QFont("Segoe UI", 10))
        
        self.playing_row = row
        if self.playing_row != -1 and self.playing_row < self.rowCount():
            font = QFont("Segoe UI", 10, QFont.Weight.Bold)
            for c in range(2):
                it = self.item(self.playing_row, c)
                if it:
                    it.setBackground(QColor("#094771"))
                    it.setFont(font)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()
        else: super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()
        else: super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if os.path.isfile(path):
                    self.add_file(path, self.window().vlc_instance)
        else:
            # Ustaw akcję Ignore, żeby Qt samo nie skasowało przeciągniętego elementu
            event.setDropAction(Qt.DropAction.IgnoreAction)
            event.accept()
            
            source_row = self.currentRow()
            pos = event.position().toPoint()
            dest_row = self.rowAt(pos.y())
            drop_indicator = self.dropIndicatorPosition()
            
            if dest_row == -1: 
                dest_row = self.rowCount()
            elif drop_indicator == QAbstractItemView.DropIndicatorPosition.BelowItem:
                dest_row += 1

            insert_row = dest_row
            if source_row < dest_row:
                insert_row -= 1

            if source_row != -1 and source_row != insert_row:
                old_playing_row = self.playing_row
                is_playing_moved = (source_row == old_playing_row)
                
                # Pobierz elementy z wiersza źródłowego (takeItem zapobiega usunięciu ich z pamięci)
                row_items = []
                for col in range(self.columnCount()):
                    row_items.append(self.takeItem(source_row, col))
                
                # Usuń stary wiersz i wstaw nowy w miejscu docelowym
                self.removeRow(source_row)
                self.insertRow(insert_row)
                
                # Wstaw elementy do nowego wiersza
                for col, item in enumerate(row_items):
                    if item:
                        self.setItem(insert_row, col, item)
                
                # Aktualizacja indeksu odtwarzania
                if is_playing_moved:
                    self.playing_row = insert_row
                elif old_playing_row != -1:
                    if source_row < old_playing_row and insert_row >= old_playing_row:
                        self.playing_row -= 1
                    elif source_row > old_playing_row and insert_row <= old_playing_row:
                        self.playing_row += 1
                
                # Odśwież wyróżnienie dla wiersza odtwarzanego
                if self.playing_row != -1:
                    font = QFont("Segoe UI", 10, QFont.Weight.Bold)
                    for c in range(2):
                        it = self.item(self.playing_row, c)
                        if it:
                            it.setBackground(QColor("#094771"))
                            it.setFont(font)
                
                self.setCurrentCell(insert_row, 0)

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Show Control - Operator Console v2.0")
        self.setMinimumSize(900, 700)
        
        try:
            self.vlc_instance = vlc.Instance('--no-xlib', '--quiet', '--vout=direct3d11', '--aout=waveout', '--video-filter=adjust')
            
            # Główny odtwarzacz (Projekcja)
            self.media_player = self.vlc_instance.media_player_new()
            self.media_player.audio_set_volume(0) 
            self.media_player.video_set_adjust_int(vlc.VideoAdjustOption.Enable, 1)
            
            # Odtwarzacz podglądu (Operator)
            self.preview_player = self.vlc_instance.media_player_new()
            self.preview_player.audio_set_volume(0) # Podgląd zawsze wyciszony
            self.preview_player.video_set_adjust_int(vlc.VideoAdjustOption.Enable, 1)
            
        except Exception as e:
            QMessageBox.critical(self, "VLC Error", f"Błąd VLC: {e}")
            sys.exit(1)
            
        self.projection_window = ProjectionWindow()
        self.projection_window.move_to_second_screen()
        self.projection_window.show()
        
        self.init_ui()
        
        if sys.platform.startswith("win"): 
            self.media_player.set_hwnd(int(self.projection_window.video_widget.winId()))
            self.preview_player.set_hwnd(int(self.preview_display.video_widget.winId()))
            
        self.media_player.video_set_mouse_input(False)
        self.media_player.video_set_key_input(False)
        self.preview_player.video_set_mouse_input(False)
        self.preview_player.video_set_key_input(False)
        self.is_playing = False
        self.is_transitioning = False
        self.user_is_seeking = False
        
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
        self.remove_btn = QPushButton("✖ Usuń")
        self.remove_btn.setToolTip("Usuń zaznaczone pliki (Delete)")
        self.remove_btn.clicked.connect(self.remove_file)
        mgmt_left.addWidget(self.add_btn)
        mgmt_left.addWidget(self.remove_btn)
        
        mgmt_right = QHBoxLayout()
        self.load_proj_btn = QPushButton("📂 Wczytaj Projekt")
        self.load_proj_btn.setToolTip("Wczytaj zapisaną listę plików")
        self.load_proj_btn.clicked.connect(self.load_project)
        self.save_proj_btn = QPushButton("💾 Zapisz Projekt")
        self.save_proj_btn.setToolTip("Zapisz aktualną listę (F12)")
        self.save_proj_btn.clicked.connect(self.save_project)
        mgmt_right.addWidget(self.load_proj_btn)
        mgmt_right.addWidget(self.save_proj_btn)
        
        top_bar.addLayout(mgmt_left)
        top_bar.addStretch()
        
        self.logo_btn = QPushButton("📁 Wybierz Logo")
        self.logo_btn.setToolTip("Wybierz grafikę do wyświetlania")
        self.logo_btn.clicked.connect(self.select_logo)
        
        self.window_btn = QPushButton("👁 Ukryj Okno")
        self.window_btn.setObjectName("HideBtn")
        self.window_btn.setToolTip("Ukryj lub pokaż okno projekcji")
        self.window_btn.clicked.connect(self.toggle_projection_window)
        
        mgmt_center = QHBoxLayout()
        mgmt_center.addWidget(self.logo_btn)
        mgmt_center.addWidget(self.window_btn)
        top_bar.addLayout(mgmt_center)
        
        top_bar.addStretch()
        top_bar.addLayout(mgmt_right)
        layout.addLayout(top_bar)

        # --- PASEK WYSZUKIWANIA ---
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Wyszukaj utwór po tytule...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.filter_playlist)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # --- PANEL ŚRODKOWY (LISTA + PODGLĄD) ---
        middle_panel = QHBoxLayout()
        
        # LISTA PLIKÓW
        self.playlist = PlaylistTable(self)
        self.playlist.itemDoubleClicked.connect(lambda: self.play_media())
        middle_panel.addWidget(self.playlist, stretch=2)
        
        # PODGLĄD OPERATORA
        self.preview_group = QGroupBox("Podgląd Na Żywo")
        preview_layout = QVBoxLayout(self.preview_group)
        self.preview_display = VideoDisplay()
        self.preview_display.setMinimumWidth(320)
        preview_layout.addWidget(self.preview_display)
        middle_panel.addWidget(self.preview_group, stretch=1)
        
        layout.addLayout(middle_panel, stretch=1)

        # --- SEKCJA TRANSPORTU ---
        transport_frame = QGroupBox("Kontrola Transportu")
        trans_layout = QVBoxLayout(transport_frame)
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.setFixedHeight(25)
        self.progress_slider.sliderMoved.connect(self.set_position)
        self.progress_slider.sliderPressed.connect(lambda: setattr(self, 'user_is_seeking', True))
        self.progress_slider.sliderReleased.connect(self.slider_released)
        
        self.time_label = QLabel("00:00 / 00:00 (Pozostało: -00:00)")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet(f"font-size: 13pt; font-weight: bold; color: {COLOR_TEXT};")
        trans_layout.addWidget(self.progress_slider)
        trans_layout.addWidget(self.time_label)
        
        btns_grid = QHBoxLayout()
        btns_grid.setSpacing(5)
        self.prev_btn = QPushButton("⏮ Poprzedni")
        self.prev_btn.setObjectName("TransportBtn")
        self.prev_btn.setToolTip("Poprzedni plik (F6 / Strzałka w lewo)")
        self.prev_btn.clicked.connect(self.play_previous_file)
        
        self.play_btn = QPushButton("▶ PLAY")
        self.play_btn.setObjectName("PlayBtn")
        self.play_btn.setToolTip("Odtwórz / Pauza (F4 / Spacja)")
        self.play_btn.clicked.connect(self.play_media)
        
        self.stop_btn = QPushButton("⏹ STOP")
        self.stop_btn.setObjectName("StopBtn")
        self.stop_btn.setToolTip("Zatrzymaj odtwarzanie (F5)")
        self.stop_btn.clicked.connect(self.stop_media)
        
        self.next_btn = QPushButton("Następny ⏭")
        self.next_btn.setObjectName("TransportBtn")
        self.next_btn.setToolTip("Następny plik (F7 / Strzałka w prawo)")
        self.next_btn.clicked.connect(self.play_next_file)
        
        for btn in [self.prev_btn, self.play_btn, self.stop_btn, self.next_btn]:
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            btns_grid.addWidget(btn)
        trans_layout.addLayout(btns_grid)
        layout.addWidget(transport_frame)

        # --- DOLNY PANEL ---
        bottom_panel = QHBoxLayout()
        view_group = QGroupBox("Widok i Efekty")
        view_layout = QVBoxLayout(view_group)
        self.fade_btn = QPushButton("✨ Fade Out")
        self.fade_btn.setObjectName("FadeBtn")
        self.fade_btn.setToolTip("Płynne wyciszenie i ściemnienie (F8)")
        self.fade_btn.clicked.connect(self.fade_out)
        self.fullscreen_btn = QPushButton("📺 Pełny Ekran")
        self.fullscreen_btn.setToolTip("Przełącz pełny ekran (F9)")
        self.fullscreen_btn.clicked.connect(self.toggle_projection_fullscreen)
        self.logo_overlay_btn = QPushButton("🖼 Logo Overlay")
        self.logo_overlay_btn.setCheckable(True)
        self.logo_overlay_btn.setToolTip("Nałóż logo na obraz (F11)")
        self.logo_overlay_btn.clicked.connect(self.toggle_logo_overlay)
        view_layout.addWidget(self.fade_btn)
        view_layout.addWidget(self.fullscreen_btn)
        view_layout.addWidget(self.logo_overlay_btn)
        
        audio_group = QGroupBox("Audio")
        audio_main_layout = QHBoxLayout(audio_group)
        
        slider_layout = QVBoxLayout()
        self.vol_label = QLabel("100%")
        self.vol_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.volume_slider = QSlider(Qt.Orientation.Vertical)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        
        slider_layout.addWidget(self.vol_label)
        slider_layout.addWidget(self.volume_slider, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        audio_main_layout.addStretch()
        audio_main_layout.addLayout(slider_layout)
        audio_main_layout.addStretch()
        
        settings_group = QGroupBox("Ustawienia")
        set_layout = QVBoxLayout(settings_group)
        self.autoplay_checkbox = QCheckBox("Autoodtwarzanie")
        self.remote_checkbox = QCheckBox("Tryb Pilota (L/P)")
        self.remote_checkbox.setChecked(True)
        self.remote_checkbox.stateChanged.connect(self.update_shortcuts)
        self.logo_audio_checkbox = QCheckBox("Logo dla Audio (F10)")
        self.logo_audio_checkbox.setChecked(True)
        self.logo_audio_checkbox.stateChanged.connect(self.update_logo_visibility)
        set_layout.addWidget(self.autoplay_checkbox)
        set_layout.addWidget(self.remote_checkbox)
        set_layout.addWidget(self.logo_audio_checkbox)
        set_layout.addStretch()
        
        bottom_panel.addWidget(view_group, stretch=1)
        bottom_panel.addWidget(audio_group, stretch=1)
        bottom_panel.addWidget(settings_group, stretch=1)
        layout.addLayout(bottom_panel)

        self.init_shortcuts()
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.check_player_status)
        self.status_timer.start(500)

    def init_shortcuts(self):
        QShortcut(QKeySequence(Qt.Key.Key_Space), self).activated.connect(self.toggle_play_pause)
        QShortcut(QKeySequence(Qt.Key.Key_Delete), self.playlist).activated.connect(self.remove_file)
        for key in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
            QShortcut(QKeySequence(key), self.playlist).activated.connect(self.play_media)
        self.sc_nav_prev = QShortcut(QKeySequence(Qt.Key.Key_Up), self)
        self.sc_nav_prev.activated.connect(self.play_previous_file)
        self.sc_nav_next = QShortcut(QKeySequence(Qt.Key.Key_Down), self)
        self.sc_nav_next.activated.connect(self.play_next_file)
        f_keys = {Qt.Key.Key_F4: self.play_media, Qt.Key.Key_F5: self.stop_media,
                  Qt.Key.Key_F6: self.play_previous_file, Qt.Key.Key_F7: self.play_next_file,
                  Qt.Key.Key_F8: self.fade_out, Qt.Key.Key_F9: self.toggle_projection_fullscreen,
                  Qt.Key.Key_F10: lambda: self.logo_audio_checkbox.setChecked(not self.logo_audio_checkbox.isChecked()),
                  Qt.Key.Key_F11: lambda: self.logo_overlay_btn.animateClick(), Qt.Key.Key_F12: self.save_project}
        for k, f in f_keys.items(): QShortcut(QKeySequence(k), self).activated.connect(f)
        self.update_shortcuts()

    def update_shortcuts(self):
        if self.remote_checkbox.isChecked():
            self.sc_nav_prev.setKey(QKeySequence(Qt.Key.Key_Left))
            self.sc_nav_next.setKey(QKeySequence(Qt.Key.Key_Right))
        else:
            self.sc_nav_prev.setKey(QKeySequence(Qt.Key.Key_Up))
            self.sc_nav_next.setKey(QKeySequence(Qt.Key.Key_Down))

    def set_volume(self, value):
        self.media_player.audio_set_volume(value)
        self.projection_window.visualizer.volume_multiplier = value / 100.0
        self.preview_display.visualizer.volume_multiplier = value / 100.0
        self.vol_label.setText(f"{value}%")

    def format_time(self, ms):
        s, _ = divmod(ms, 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

    def check_player_status(self):
        if self.is_playing and not self.is_transitioning:
            state = self.media_player.get_state()
            if state in (vlc.State.Ended, vlc.State.Stopped):
                self.is_playing = False
                if state == vlc.State.Ended and self.autoplay_checkbox.isChecked(): self.play_next_file()
            if not self.user_is_seeking:
                pos = self.media_player.get_position()
                if pos >= 0: self.progress_slider.setValue(int(pos * 1000))
                curr, total = self.media_player.get_time(), self.media_player.get_length()
                if curr >= 0 and total >= 0:
                    rem = max(0, total - curr)
                    self.time_label.setText(f"{self.format_time(curr)} / {self.format_time(total)} (Pozostało: -{self.format_time(rem)})")
        elif not self.user_is_seeking:
            self.progress_slider.setValue(0)
            self.time_label.setText("00:00 / 00:00 (Pozostało: -00:00)")

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Dodaj multimedia", "", "Media (*.mp4 *.mp3 *.mkv *.jpg *.png);;Wszystkie (*.*)")
        for f in files: self.playlist.add_file(f, self.vlc_instance)

    def remove_file(self):
        for item in self.playlist.selectedItems(): self.playlist.removeRow(item.row())

    def play_media(self):
        row = self.playlist.currentRow()
        if row == -1 or self.is_transitioning: return
        path = self.playlist.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.playlist.set_playing_row(row)
        
        is_audio = path.lower().endswith(('.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'))
        
        if self.logo_overlay_btn.isChecked() or is_audio: 
            self.projection_window.set_mode_audio()
            self.preview_display.set_mode_audio()
        else:
            self.projection_window.set_mode_video()
            self.preview_display.set_mode_video()
            
        threading.Thread(target=self._transition_thread, args=(path,), daemon=True).start()

    def _transition_thread(self, path):
        self.is_transitioning = True
        target_vol = self.volume_slider.value()
        try:
            if self.is_playing:
                has_audio = (self.media_player.audio_get_track_count() > 0)
                start_vol = self.media_player.audio_get_volume() if has_audio else 0
                for i in range(20):
                    vol = start_vol * (1 - (i + 1) / 20.0)
                    bri = 1.0 - ((i + 1) * 0.05)
                    if has_audio: self.media_player.audio_set_volume(int(max(0, vol)))
                    self.media_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, max(0.0, bri))
                    self.preview_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, max(0.0, bri))
                    time.sleep(0.05)
                # Upewniamy się że zeszło do magicznego zera. ŻADNEGO UŻYWANIA MUTE! (Mute popuje na Win32)
                if has_audio:
                    self.media_player.audio_set_volume(0)
                
                self.media_player.pause() 
                self.preview_player.pause()
                time.sleep(0.1)
                self.media_player.stop()
                self.preview_player.stop()
                
            media = self.vlc_instance.media_new(path)
            self.media_player.set_media(media)
            self.preview_player.set_media(media)
            
            self.media_player.play()
            self.preview_player.play()
            self.is_playing = True
            
            # Poczekaj aż faktycznie zacznie odtwarzać
            for _ in range(50):
                if self.media_player.get_state() == vlc.State.Playing:
                    break
                time.sleep(0.01)
                
            time.sleep(0.1) 
            self.media_player.video_set_adjust_int(vlc.VideoAdjustOption.Enable, 1)
            self.preview_player.video_set_adjust_int(vlc.VideoAdjustOption.Enable, 1)
            
            has_audio = (self.media_player.audio_get_track_count() > 0)
            
            for i in range(20):
                vol = target_vol * ((i + 1) / 20.0)
                bri = (i + 1) * 0.05
                if has_audio: self.media_player.audio_set_volume(int(min(target_vol, vol)))
                self.media_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, min(1.0, bri))
                self.preview_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, min(1.0, bri))
                time.sleep(0.02)
        except: pass
        self.is_transitioning = False


    def fade_out(self):
        if self.is_playing and not self.is_transitioning:
            threading.Thread(target=self._fade_out_thread, daemon=True).start()

    def _fade_out_thread(self):
        self.is_transitioning = True
        has_audio = (self.media_player.audio_get_track_count() > 0)
        start_vol = self.media_player.audio_get_volume() if has_audio else 0
        for i in range(40):
            vol = start_vol * (1 - (i + 1) / 40.0)
            bri = 1.0 - ((i + 1) * 0.025)
            if has_audio: self.media_player.audio_set_volume(int(max(0, vol)))
            self.media_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, max(0.0, bri))
            self.preview_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, max(0.0, bri))
            time.sleep(0.05)
            
        self.stop_media()
        
        self.media_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, 1.0)
        self.preview_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, 1.0)
        self.is_transitioning = False

    def toggle_play_pause(self):
        if self.is_playing:
            if self.media_player.get_state() == vlc.State.Playing:
                self.media_player.pause()
                self.preview_player.pause()
            else:
                self.media_player.play()
                self.preview_player.play()
        else: self.play_media()

    def stop_media(self):
        if self.media_player.get_state() in (vlc.State.Playing, vlc.State.Paused):
            self.media_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, 0.0)
            self.preview_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, 0.0)
            
            has_audio = (self.media_player.audio_get_track_count() > 0)
            if has_audio:
                self.media_player.audio_set_volume(0)
                
            self.media_player.pause()
            self.preview_player.pause()
            time.sleep(0.05) 
            
        self.media_player.stop()
        self.preview_player.stop()
        self.is_playing = False
        self.playlist.set_playing_row(-1)

    def play_next_file(self):
        if self.playlist.currentRow() < self.playlist.rowCount() - 1:
            self.playlist.setCurrentCell(self.playlist.currentRow() + 1, 0)
            self.play_media()

    def play_previous_file(self):
        if self.playlist.currentRow() > 0:
            self.playlist.setCurrentCell(self.playlist.currentRow() - 1, 0)
            self.play_media()

    def select_logo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Logo", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if path:
            pixmap = QPixmap(path)
            self.projection_window.visualizer.logo_pixmap = pixmap
            self.preview_display.visualizer.logo_pixmap = pixmap

    def toggle_projection_fullscreen(self):
        if self.projection_window.isFullScreen(): self.projection_window.showNormal()
        else: self.projection_window.showFullScreen()
        
        if sys.platform.startswith("win"):
            self.media_player.set_hwnd(int(self.projection_window.video_widget.winId()))
            
        self.activateWindow()

    def toggle_projection_window(self):
        if self.projection_window.isVisible():
            self.projection_window.hide()
        else:
            self.projection_window.show()
            if sys.platform.startswith("win"):
                self.media_player.set_hwnd(int(self.projection_window.video_widget.winId()))

    def toggle_logo_overlay(self, checked):
        if checked: 
            self.projection_window.set_mode_audio()
            self.preview_display.set_mode_audio()
        else:
            row = self.playlist.currentRow()
            if row != -1:
                path = self.playlist.item(row, 0).data(Qt.ItemDataRole.UserRole)
                is_audio = path.lower().endswith(('.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'))
                if is_audio:
                    self.projection_window.set_mode_audio()
                    self.preview_display.set_mode_audio()
                else:
                    self.projection_window.set_mode_video()
                    self.preview_display.set_mode_video()
            else: 
                self.projection_window.set_mode_video()
                self.preview_display.set_mode_video()

    def update_logo_visibility(self): 
        visible = self.logo_audio_checkbox.isChecked()
        self.projection_window.visualizer.show_logo = visible
        self.preview_display.visualizer.show_logo = visible
        
    def set_position(self, v):
        pos = v / 1000.0
        self.media_player.set_position(pos)
        self.preview_player.set_position(pos)

    def slider_released(self): self.user_is_seeking = False; self.set_position(self.progress_slider.value())
    
    def filter_playlist(self, text):
        search_text = text.lower()
        for row in range(self.playlist.rowCount()):
            item = self.playlist.item(row, 0)
            if item: self.playlist.setRowHidden(row, search_text not in item.text().lower())

    def save_project(self):
        path, _ = QFileDialog.getSaveFileName(self, "Zapisz", "", "JSON (*.json)")
        if path:
            items = [self.playlist.item(i, 0).data(Qt.ItemDataRole.UserRole) for i in range(self.playlist.rowCount())]
            with open(path, 'w', encoding='utf-8') as f: json.dump(items, f, ensure_ascii=False, indent=4)

    def load_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "Wczytaj", "", "JSON (*.json)")
        if path:
            with open(path, 'r', encoding='utf-8') as f: items = json.load(f)
            self.playlist.setRowCount(0)
            for p in items: self.playlist.add_file(p, self.vlc_instance)

    def closeEvent(self, event): self.projection_window.close(); super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)
    window = App()
    window.show()
    sys.exit(app.exec())
