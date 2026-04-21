# Show-control
# Copyright (C) 2026 Piotr
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
    print("Error: python-vlc library is not installed.")
    print("Install it using: pip install python-vlc")
    sys.exit(1)

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QSlider, QListWidget, 
                             QFileDialog, QMessageBox, QCheckBox, QStackedLayout,
                             QLabel, QListWidgetItem, QFrame)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QShortcut, QKeySequence, QPainter, QColor, QPixmap, QFont

# --- UI STYLE CONFIGURATION ---
UI_STYLES = {
    "colors": {
        "bg_main": "#1e1e1e",
        "bg_dark": "#252526",
        "bg_sidebar": "#2d2d2d",
        "text_main": "#d4d4d4",
        "text_dim": "#aaaaaa",
        "accent": "#007acc",
        "accent_hover": "#1c97ea",
        "play": "#2d8a49",
        "stop": "#a1260d",
        "fade": "#d18616",
        "item_playing": "#094771",
        "border": "#3c3c3c"
    },
    "fonts": {
        "main": "Segoe UI",
        "size_normal": 10,
        "size_large": 12,
        "size_huge": 14
    }
}

APP_STYLESHEET = f"""
    QMainWindow, QWidget {{
        background-color: {UI_STYLES['colors']['bg_main']};
        color: {UI_STYLES['colors']['text_main']};
        font-family: '{UI_STYLES['fonts']['main']}', system-ui;
        font-size: {UI_STYLES['fonts']['size_normal']}pt;
    }}
    
    QLabel {{ color: {UI_STYLES['colors']['text_dim']}; }}
    
    QFrame#SectionFrame {{
        border: 1px solid {UI_STYLES['colors']['border']};
        border-radius: 4px;
        background-color: {UI_STYLES['colors']['bg_dark']};
        margin: 2px;
    }}
    
    QPushButton {{
        background-color: {UI_STYLES['colors']['bg_sidebar']};
        border: 1px solid {UI_STYLES['colors']['border']};
        padding: 8px 15px;
        border-radius: 3px;
        min-height: 20px;
    }}
    QPushButton:hover {{ background-color: #3e3e42; }}
    QPushButton:pressed {{ background-color: {UI_STYLES['colors']['accent']}; }}
    
    QPushButton#PlayBtn {{ 
        background-color: {UI_STYLES['colors']['play']}; 
        font-weight: bold; 
        font-size: {UI_STYLES['fonts']['size_large']}pt;
        min-height: 40px;
    }}
    QPushButton#PlayBtn:hover {{ background-color: #3aa659; }}
    
    QPushButton#StopBtn {{ 
        background-color: {UI_STYLES['colors']['stop']}; 
        font-weight: bold;
        font-size: {UI_STYLES['fonts']['size_large']}pt;
        min-height: 40px;
    }}
    QPushButton#StopBtn:hover {{ background-color: #be2d10; }}
    
    QPushButton#TransportBtn {{
        font-weight: bold;
        font-size: {UI_STYLES['fonts']['size_large']}pt;
        min-height: 40px;
    }}

    QPushButton#FadeBtn {{ background-color: {UI_STYLES['colors']['fade']}; }}
    QPushButton#FadeBtn:hover {{ background-color: #e5951a; }}
    
    QListWidget {{
        background-color: {UI_STYLES['colors']['bg_dark']};
        border: 1px solid {UI_STYLES['colors']['border']};
        outline: none;
    }}
    QListWidget::item {{
        padding: 10px;
        border-bottom: 1px solid #2d2d2d;
    }}
    QListWidget::item:alternate {{ background-color: #2a2a2d; }}
    QListWidget::item:selected {{
        background-color: {UI_STYLES['colors']['accent']};
        color: white;
    }}
    
    QSlider::groove:horizontal {{
        border: 1px solid {UI_STYLES['colors']['border']};
        height: 8px;
        background: {UI_STYLES['colors']['bg_dark']};
        border-radius: 4px;
    }}
    QSlider::handle:horizontal {{
        background: {UI_STYLES['colors']['accent']};
        width: 18px;
        height: 18px;
        margin: -6px 0;
        border-radius: 9px;
    }}
    
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        background-color: {UI_STYLES['colors']['bg_dark']};
        border: 1px solid {UI_STYLES['colors']['border']};
        border-radius: 3px;
    }}
    QCheckBox::indicator:checked {{
        background-color: {UI_STYLES['colors']['accent']};
        image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPjxwYXRoIGQ9Ik05IDE2LjE3TDQuODMgMTJsLTEuNDIgMS40MUw5IDE5IDIxIDdsLTEuNDEtMS40MXoiLz48L3N2Zz4=);
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
        for i in range(self.bars):
            self.heights[i] = 0
            self.targets[i] = 0
        self.timer.start(50)
        self.show()
        
    def stop(self):
        self.is_active = False
        self.timer.stop()
        for i in range(self.bars):
            self.heights[i] = 0
            self.targets[i] = 0
        self.update()
        self.hide()
        
    def update_bars(self):
        if not self.is_active: return
        for i in range(self.bars):
            if random.random() < 0.2:
                center_factor = math.sin((i / (self.bars - 1)) * math.pi)
                base_rand = random.random()
                self.targets[i] = (base_rand * base_rand * 100 * center_factor + 10) * self.volume_multiplier
            else:
                self.targets[i] *= 0.8
            diff = self.targets[i] - self.heights[i]
            self.heights[i] += diff * 0.4
        self.update()

    def paintEvent(self, event):
        if not self.is_active: return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        if self.show_logo and self.logo_pixmap and not self.logo_pixmap.isNull():
            scaled = self.logo_pixmap.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            px = int((w - scaled.width()) / 2)
            py = int((h - scaled.height()) / 2)
            painter.drawPixmap(px, py, scaled)

class ProjectionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.Window)
        self.setWindowTitle("Projection Output")
        self.setStyleSheet("background-color: black;")
        self.video_widget = QWidget()
        self.video_widget.setStyleSheet("background-color: black;")
        self.vis_container = QWidget()
        self.vis_container.setStyleSheet("background-color: black;")
        vis_layout = QVBoxLayout(self.vis_container)
        vis_layout.setContentsMargins(0, 0, 0, 0)
        self.visualizer = AudioVisualizer()
        vis_layout.addWidget(self.visualizer)
        self.stacked_layout = QStackedLayout(self)
        self.stacked_layout.setContentsMargins(0, 0, 0, 0)
        self.stacked_layout.addWidget(self.video_widget)
        self.stacked_layout.addWidget(self.vis_container)
        self.set_mode_video()

    def set_mode_video(self):
        self.stacked_layout.setCurrentWidget(self.video_widget)
        self.visualizer.stop()
        
    def set_mode_audio(self):
        self.stacked_layout.setCurrentWidget(self.vis_container)
        self.visualizer.start()
        
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.isFullScreen(): self.showNormal()
            else: self.showFullScreen()
            event.accept()

    def move_to_second_screen(self):
        screens = QApplication.screens()
        if len(screens) > 1:
            second_screen = screens[1]
            self.resize(800, 600)
            self.move(second_screen.geometry().topLeft() + second_screen.geometry().center() - self.rect().center())
            self.showFullScreen()
        else:
            self.resize(800, 600)

class PlaylistWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.setAlternatingRowColors(True)
        self.playing_item = None

    def add_file(self, file_path):
        filename = os.path.basename(file_path)
        item = QListWidgetItem(filename)
        item.setData(Qt.ItemDataRole.UserRole, file_path)
        item.setToolTip(file_path)
        self.addItem(item)

    def set_playing(self, item):
        if self.playing_item:
            self.playing_item.setBackground(QColor("transparent"))
            self.playing_item.setFont(QFont(UI_STYLES['fonts']['main']))
        self.playing_item = item
        if self.playing_item:
            self.playing_item.setBackground(QColor(UI_STYLES['colors']['item_playing']))
            font = QFont(UI_STYLES['fonts']['main'])
            font.setBold(True)
            self.playing_item.setFont(font)

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
                file_path = url.toLocalFile()
                if os.path.isfile(file_path): self.add_file(file_path)
        else: super().dropEvent(event)

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Show Control - Operator Console")
        self.setMinimumSize(800, 650)
        
        try:
            self.vlc_instance = vlc.Instance('--no-xlib', '--quiet', '--vout=direct3d9', '--video-filter=adjust')
            self.media_player = self.vlc_instance.media_player_new()
            self.media_player.video_set_adjust_int(vlc.VideoAdjustOption.Enable, 1)
        except Exception as e:
            QMessageBox.critical(self, "VLC Error", f"Failed to initialize VLC: {e}")
            sys.exit(1)
            
        self.projection_window = ProjectionWindow()
        self.projection_window.move_to_second_screen()
        self.projection_window.show()
        
        if sys.platform.startswith("win"):
            self.media_player.set_hwnd(int(self.projection_window.video_widget.winId()))
        elif sys.platform.startswith("linux"):
            self.media_player.set_xwindow(int(self.projection_window.video_widget.winId()))
        elif sys.platform == "darwin":
            self.media_player.set_nsobject(int(self.projection_window.video_widget.winId()))
            
        self.media_player.video_set_mouse_input(False)
        self.media_player.video_set_key_input(False)
            
        self.init_ui()
        self.is_playing = False
        self.is_transitioning = False
        self.user_is_seeking = False
        
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # --- MANAGEMENT SECTION (TOP) ---
        mgmt_frame = QFrame()
        mgmt_frame.setObjectName("SectionFrame")
        mgmt_layout = QHBoxLayout(mgmt_frame)
        
        self.add_btn = QPushButton("Add Files")
        self.add_btn.setToolTip("Add new media files to playlist")
        self.add_btn.clicked.connect(self.add_files)
        
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.setToolTip("Remove selected files (Delete)")
        self.remove_btn.clicked.connect(self.remove_file)
        
        self.load_proj_btn = QPushButton("Load Project")
        self.load_proj_btn.clicked.connect(self.load_project)
        
        self.save_proj_btn = QPushButton("Save Project")
        self.save_proj_btn.setToolTip("Save current playlist (F12)")
        self.save_proj_btn.clicked.connect(self.save_project)
        
        mgmt_layout.addWidget(self.add_btn)
        mgmt_layout.addWidget(self.remove_btn)
        mgmt_layout.addStretch()
        mgmt_layout.addWidget(self.load_proj_btn)
        mgmt_layout.addWidget(self.save_proj_btn)
        main_layout.addWidget(mgmt_frame)

        # --- PLAYLIST ---
        self.playlist = PlaylistWidget()
        self.playlist.itemDoubleClicked.connect(lambda: self.play_media())
        main_layout.addWidget(self.playlist, stretch=1)

        # --- TRANSPORT SECTION (MIDDLE) ---
        transport_frame = QFrame()
        transport_frame.setObjectName("SectionFrame")
        transport_layout = QVBoxLayout(transport_frame)
        
        prog_layout = QVBoxLayout()
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.setFixedHeight(25)
        self.progress_slider.sliderMoved.connect(self.set_position)
        self.progress_slider.sliderPressed.connect(self.slider_pressed)
        self.progress_slider.sliderReleased.connect(self.slider_released)
        
        self.time_info_label = QLabel("00:00 / 00:00 (Remaining: 00:00)")
        self.time_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_info_label.setStyleSheet(f"font-size: {UI_STYLES['fonts']['size_large']}pt; font-weight: bold;")
        
        prog_layout.addWidget(self.progress_slider)
        prog_layout.addWidget(self.time_info_label)
        transport_layout.addLayout(prog_layout)
        
        btns_row = QHBoxLayout()
        self.prev_btn = QPushButton("⏮ Previous")
        self.prev_btn.setObjectName("TransportBtn")
        self.prev_btn.setToolTip("Previous file (F6 / Left Arrow)")
        self.prev_btn.clicked.connect(self.play_previous_file)
        
        self.play_btn = QPushButton("▶ PLAY")
        self.play_btn.setObjectName("PlayBtn")
        self.play_btn.setToolTip("Play / Pause (F4 / Space)")
        self.play_btn.clicked.connect(self.play_media)
        
        self.stop_btn = QPushButton("⏹ STOP")
        self.stop_btn.setObjectName("StopBtn")
        self.stop_btn.setToolTip("Stop playback (F5)")
        self.stop_btn.clicked.connect(self.stop_media)
        
        self.next_btn = QPushButton("Next ⏭")
        self.next_btn.setObjectName("TransportBtn")
        self.next_btn.setToolTip("Next file (F7 / Right Arrow)")
        self.next_btn.clicked.connect(self.play_next_file)
        
        btns_row.addWidget(self.prev_btn)
        btns_row.addWidget(self.play_btn)
        btns_row.addWidget(self.stop_btn)
        btns_row.addWidget(self.next_btn)
        transport_layout.addLayout(btns_row)
        main_layout.addWidget(transport_frame)

        # --- EFFECTS & VIEW SECTION (BOTTOM) ---
        bottom_frame = QFrame()
        bottom_frame.setObjectName("SectionFrame")
        bottom_layout = QHBoxLayout(bottom_frame)
        
        effects_col = QVBoxLayout()
        self.fade_btn = QPushButton("✨ Fade Out")
        self.fade_btn.setObjectName("FadeBtn")
        self.fade_btn.setToolTip("Smooth volume fade out (F8)")
        self.fade_btn.clicked.connect(self.fade_out)
        
        self.logo_overlay_btn = QPushButton("🖼 Logo Overlay")
        self.logo_overlay_btn.setCheckable(True)
        self.logo_overlay_btn.setToolTip("Overlay logo on video (F11)")
        self.logo_overlay_btn.clicked.connect(self.toggle_logo_overlay)
        
        effects_col.addWidget(self.fade_btn)
        effects_col.addWidget(self.logo_overlay_btn)
        
        view_col = QVBoxLayout()
        self.fullscreen_btn = QPushButton("📺 Fullscreen")
        self.fullscreen_btn.setToolTip("Toggle fullscreen mode (F9)")
        self.fullscreen_btn.clicked.connect(self.toggle_projection_fullscreen)
        
        self.window_btn = QPushButton("👁 Hide Window")
        self.window_btn.clicked.connect(self.toggle_projection_window)
        
        view_col.addWidget(self.fullscreen_btn)
        view_col.addWidget(self.window_btn)
        
        settings_col = QVBoxLayout()
        vol_layout = QHBoxLayout()
        vol_layout.addWidget(QLabel("Volume:"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setFixedHeight(25)
        self.volume_slider.valueChanged.connect(self.set_volume)
        vol_layout.addWidget(self.volume_slider)
        
        logo_opt_layout = QHBoxLayout()
        self.logo_checkbox = QCheckBox("Logo for Audio (F10)")
        self.logo_checkbox.setChecked(True)
        self.logo_checkbox.stateChanged.connect(self.update_logo_visibility)
        
        self.logo_btn = QPushButton("Select Logo")
        self.logo_btn.clicked.connect(self.select_logo)
        
        logo_opt_layout.addWidget(self.logo_checkbox)
        logo_opt_layout.addWidget(self.logo_btn)
        
        self.autoplay_checkbox = QCheckBox("Autoplay next item")
        self.remote_mode_checkbox = QCheckBox("Remote mode (Left/Right)")
        self.remote_mode_checkbox.setChecked(True)
        self.remote_mode_checkbox.stateChanged.connect(self.update_shortcuts)
        
        settings_col.addLayout(vol_layout)
        settings_col.addLayout(logo_opt_layout)
        check_row = QHBoxLayout()
        check_row.addWidget(self.autoplay_checkbox)
        check_row.addWidget(self.remote_mode_checkbox)
        settings_col.addLayout(check_row)
        
        bottom_layout.addLayout(effects_col)
        bottom_layout.addLayout(view_col)
        bottom_layout.addLayout(settings_col)
        main_layout.addWidget(bottom_frame)

        self.init_shortcuts()
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.check_player_status)
        self.status_timer.start(500)

    def init_shortcuts(self):
        self.sc_space = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        self.sc_space.activated.connect(self.toggle_play_pause)
        for key in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
            sc = QShortcut(QKeySequence(key), self.playlist)
            sc.activated.connect(self.play_media)
        self.sc_del = QShortcut(QKeySequence(Qt.Key.Key_Delete), self.playlist)
        self.sc_del.activated.connect(self.remove_file)
        self.sc_nav_prev = QShortcut(QKeySequence(Qt.Key.Key_Up), self)
        self.sc_nav_prev.activated.connect(self.play_previous_file)
        self.sc_nav_next = QShortcut(QKeySequence(Qt.Key.Key_Down), self)
        self.sc_nav_next.activated.connect(self.play_next_file)
        shortcuts = {
            Qt.Key.Key_F4: self.play_media, Qt.Key.Key_F5: self.stop_media,
            Qt.Key.Key_F6: self.play_previous_file, Qt.Key.Key_F7: self.play_next_file,
            Qt.Key.Key_F8: self.fade_out, Qt.Key.Key_F9: self.toggle_projection_fullscreen,
            Qt.Key.Key_F10: self.toggle_logo_checkbox, Qt.Key.Key_F11: lambda: self.logo_overlay_btn.animateClick(),
            Qt.Key.Key_F12: self.save_project
        }
        for key, func in shortcuts.items():
            sc = QShortcut(QKeySequence(key), self)
            sc.activated.connect(func)
        self.update_shortcuts()

    def update_shortcuts(self):
        if self.remote_mode_checkbox.isChecked():
            self.sc_nav_prev.setKey(QKeySequence(Qt.Key.Key_Left))
            self.sc_nav_next.setKey(QKeySequence(Qt.Key.Key_Right))
        else:
            self.sc_nav_prev.setKey(QKeySequence(Qt.Key.Key_Up))
            self.sc_nav_next.setKey(QKeySequence(Qt.Key.Key_Down))
        
    def select_logo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Logo", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if path:
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self.projection_window.visualizer.logo_pixmap = pixmap
                QMessageBox.information(self, "Success", "Logo loaded successfully.")
                
    def update_logo_visibility(self):
        self.projection_window.visualizer.show_logo = self.logo_checkbox.isChecked()

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files", "", "Media (*.mp4 *.mp3 *.mkv *.jpg *.png);;All (*.*)")
        for f in files: self.playlist.add_file(f)

    def remove_file(self):
        for item in self.playlist.selectedItems(): self.playlist.takeItem(self.playlist.row(item))

    def format_time(self, ms):
        s, _ = divmod(ms, 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

    def slider_pressed(self): self.user_is_seeking = True
    def slider_released(self):
        self.user_is_seeking = False
        self.media_player.set_position(self.progress_slider.value() / 1000.0)

    def set_position(self, value):
        total = self.media_player.get_length()
        if total > 0:
            current_ms = int((value / 1000.0) * total)
            self._update_time_label(current_ms, total)

    def _update_time_label(self, current, total):
        rem = max(0, total - current)
        self.time_info_label.setText(f"{self.format_time(current)} / {self.format_time(total)} (Remaining: -{self.format_time(rem)})")

    def check_player_status(self):
        if self.is_playing:
            if not self.is_transitioning:
                state = self.media_player.get_state()
                if state in (vlc.State.Ended, vlc.State.Stopped):
                    self.is_playing = False
                    if state == vlc.State.Ended and self.autoplay_checkbox.isChecked(): self.play_next_file()
            if not self.user_is_seeking:
                pos = self.media_player.get_position()
                if pos >= 0: self.progress_slider.setValue(int(pos * 1000))
                curr = self.media_player.get_time()
                total = self.media_player.get_length()
                if curr >= 0 and total >= 0: self._update_time_label(curr, total)
        else:
            if not self.user_is_seeking:
                self.progress_slider.setValue(0)
                self.time_info_label.setText("00:00 / 00:00 (Remaining: 00:00)")

    def play_next_file(self):
        row = self.playlist.currentRow()
        if row < self.playlist.count() - 1:
            self.playlist.setCurrentRow(row + 1)
            self.play_media()

    def play_previous_file(self):
        row = self.playlist.currentRow()
        if row > 0:
            self.playlist.setCurrentRow(row - 1)
            self.play_media()

    def save_project(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "Project (*.json)")
        if path:
            items = [self.playlist.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.playlist.count())]
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=4)

    def load_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Project", "", "Project (*.json)")
        if path:
            with open(path, 'r', encoding='utf-8') as f: items = json.load(f)
            self.playlist.clear()
            for item_path in items: self.playlist.add_file(item_path)

    def play_media(self):
        item = self.playlist.currentItem()
        if not item or self.is_transitioning: return
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Error", "File does not exist.")
            return
        self.playlist.set_playing(item)
        if self.logo_overlay_btn.isChecked(): self.projection_window.set_mode_audio()
        else:
            is_audio = file_path.lower().endswith(('.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'))
            self.projection_window.set_mode_audio() if is_audio else self.projection_window.set_mode_video()
        threading.Thread(target=self._play_transition_thread, args=(file_path,), daemon=True).start()

    def _play_transition_thread(self, file_path):
        self.is_transitioning = True
        target_vol = self.volume_slider.value()
        try:
            if self.is_playing:
                vol = self.media_player.audio_get_volume()
                if vol < 0: vol = target_vol
                brightness = 1.0
                steps = 20
                for _ in range(steps):
                    vol -= (vol / steps)
                    brightness -= (1.0 / steps)
                    self.media_player.audio_set_volume(int(max(0, vol)))
                    self.media_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, float(max(0.0, brightness)))
                    time.sleep(0.05)
                self.media_player.stop()
            
            # Reset before new file
            self.media_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, 0.0)
            
            media = self.vlc_instance.media_new(file_path)
            self.media_player.set_media(media)
            self.media_player.play()
            self.is_playing = True
            time.sleep(0.2)
            
            self.media_player.video_set_adjust_int(vlc.VideoAdjustOption.Enable, 1)
            
            vol = 0
            brightness = 0.0
            for _ in range(20):
                vol += (target_vol / 20)
                brightness += (1.0 / 20)
                self.media_player.audio_set_volume(int(min(target_vol, vol)))
                self.media_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, float(min(1.0, brightness)))
                self.projection_window.visualizer.volume_multiplier = vol / 100.0
                time.sleep(0.02)
                
            self.media_player.audio_set_volume(target_vol)
            self.media_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, 1.0)
        except Exception as e: print(f"Thread Error: {e}")
        self.is_transitioning = False

    def toggle_play_pause(self):
        if self.is_playing: self.media_player.pause() if self.media_player.get_state() == vlc.State.Playing else self.media_player.play()
        else: self.play_media()

    def stop_media(self):
        self.media_player.stop()
        self.is_playing = False
        self.playlist.set_playing(None)

    def fade_out(self):
        if self.is_playing and not self.is_transitioning:
            threading.Thread(target=self._fade_out_thread, daemon=True).start()
        
    def _fade_out_thread(self):
        self.is_transitioning = True
        vol = self.media_player.audio_get_volume()
        if vol < 0: vol = self.volume_slider.value()
        brightness = 1.0
        steps = 40
        for i in range(steps):
            vol -= (vol / (steps - i))
            brightness -= (1.0 / steps)
            self.media_player.audio_set_volume(int(max(0, vol)))
            self.media_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, float(max(0.0, brightness)))
            self.projection_window.visualizer.volume_multiplier = vol / 100.0
            time.sleep(0.05)
        self.stop_media()
        self.media_player.audio_set_volume(self.volume_slider.value())
        self.media_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, 1.0)
        self.is_transitioning = False

    def toggle_projection_fullscreen(self):
        if self.projection_window.isFullScreen(): self.projection_window.showNormal()
        else: self.projection_window.showFullScreen()
        self.activateWindow()
        self.raise_()

    def toggle_projection_window(self):
        if self.projection_window.isVisible():
            self.projection_window.hide()
            self.window_btn.setText("👁 Show Window")
        else:
            self.projection_window.show()
            self.window_btn.setText("👁 Hide Window")

    def toggle_logo_overlay(self, checked):
        if checked:
            self.projection_window.set_mode_audio()
        else:
            # Restore mode based on current file type without restarting playback
            item = self.playlist.currentItem()
            if item:
                file_path = item.data(Qt.ItemDataRole.UserRole)
                is_audio = file_path.lower().endswith(('.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'))
                if is_audio:
                    self.projection_window.set_mode_audio()
                else:
                    self.projection_window.set_mode_video()
            else:
                self.projection_window.set_mode_video()

    def toggle_logo_checkbox(self): self.logo_checkbox.setChecked(not self.logo_checkbox.isChecked())

    def set_volume(self, value):
        try:
            self.media_player.audio_set_volume(value)
            self.projection_window.visualizer.volume_multiplier = value / 100.0
        except Exception: pass

    def closeEvent(self, event):
        self.projection_window.close()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)
    window = App()
    window.show()
    sys.exit(app.exec())
