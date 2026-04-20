import sys
import os
import time
import threading
import json

try:
    import vlc
except ImportError:
    print("Error: python-vlc library is not installed.")
    print("Install it using: pip install python-vlc")
    sys.exit(1)

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QSlider, QListWidget, 
                             QFileDialog, QMessageBox, QCheckBox, QStackedLayout,
                             QLabel)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QShortcut, QKeySequence, QPainter, QColor, QLinearGradient, QBrush, QPixmap
import random
import math

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
        if not self.is_active:
            return
            
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
        if not self.is_active:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # Draw background (logo)
        if self.show_logo and getattr(self, 'logo_pixmap', None) and not self.logo_pixmap.isNull():
            scaled_pixmap = self.logo_pixmap.scaled(
                w, h, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            px = int((w - scaled_pixmap.width()) / 2)
            py = int((h - scaled_pixmap.height()) / 2)
            
            painter.drawPixmap(px, py, scaled_pixmap)

class ProjectionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.Window)
        self.setWindowTitle("Projection - Media Player")
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
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
            event.accept()

    def move_to_second_screen(self):
        screens = QApplication.screens()
        if len(screens) > 1:
            second_screen = screens[1]
            self.resize(800, 600)
            self.move(second_screen.geometry().topLeft() + second_screen.geometry().center() - self.rect().center())
            self.showFullScreen()
        else:
            self.setWindowTitle("Projection Output")
            self.resize(800, 600)

class PlaylistWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    self.addItem(file_path)
        else:
            super().dropEvent(event)

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Show Control - Operator Console")
        self.setGeometry(100, 100, 700, 500)
        
        try:
            self.vlc_instance = vlc.Instance('--no-xlib', '--quiet', '--vout=direct3d9', '--video-filter=adjust')
            self.media_player = self.vlc_instance.media_player_new()
            self.media_player.video_set_adjust_int(vlc.VideoAdjustOption.Enable, 1)
        except Exception as e:
            QMessageBox.critical(self, "VLC Engine Error", f"Could not initialize VLC engine:\n{e}\nPlease ensure VLC media player is installed correctly.")
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
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        
        # Playlist Header
        layout.addWidget(QLabel("Media Playlist (Drag & Drop supported):"))
        self.playlist = PlaylistWidget()
        self.playlist.itemDoubleClicked.connect(lambda item: self.play_media())
        layout.addWidget(self.playlist)
        
        # Project Management (Row 1)
        project_btn_layout = QHBoxLayout()
        
        self.save_proj_btn = QPushButton("Save Project (F12)")
        self.save_proj_btn.clicked.connect(self.save_project)
        project_btn_layout.addWidget(self.save_proj_btn)
        
        self.load_proj_btn = QPushButton("Load Project")
        self.load_proj_btn.clicked.connect(self.load_project)
        project_btn_layout.addWidget(self.load_proj_btn)

        self.add_btn = QPushButton("Add Media")
        self.add_btn.clicked.connect(self.add_files)
        project_btn_layout.addWidget(self.add_btn)
        
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self.remove_file)
        project_btn_layout.addWidget(self.remove_btn)
        
        layout.addLayout(project_btn_layout)

        # Navigation (Row 2)
        nav_btn_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("<< Previous (F6)")
        self.prev_btn.clicked.connect(self.play_previous_file)
        nav_btn_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("Next >> (F7)")
        self.next_btn.clicked.connect(self.play_next_file)
        nav_btn_layout.addWidget(self.next_btn)

        layout.addLayout(nav_btn_layout)
        
        # Transport & Display Controls (Row 3)
        btn_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("Play (F4)")
        self.play_btn.clicked.connect(self.play_media)
        btn_layout.addWidget(self.play_btn)
        
        self.stop_btn = QPushButton("Stop (F5)")
        self.stop_btn.clicked.connect(self.stop_media)
        btn_layout.addWidget(self.stop_btn)
        
        self.fade_btn = QPushButton("Fade Out (F8)")
        self.fade_btn.clicked.connect(self.fade_out)
        btn_layout.addWidget(self.fade_btn)
        
        self.fullscreen_btn = QPushButton("Fullscreen (F9)")
        self.fullscreen_btn.clicked.connect(self.toggle_projection_fullscreen)
        btn_layout.addWidget(self.fullscreen_btn)
        
        self.window_btn = QPushButton("Hide Window")
        self.window_btn.clicked.connect(self.toggle_projection_window)
        btn_layout.addWidget(self.window_btn)
        
        self.logo_overlay_btn = QPushButton("Logo Overlay (F11)")
        self.logo_overlay_btn.setCheckable(True)
        self.logo_overlay_btn.clicked.connect(self.toggle_logo_overlay)
        btn_layout.addWidget(self.logo_overlay_btn)
        
        layout.addLayout(btn_layout)

        # Progress bar
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.sliderMoved.connect(self.set_position)
        self.progress_slider.sliderPressed.connect(self.slider_pressed)
        self.progress_slider.sliderReleased.connect(self.slider_released)
        layout.addWidget(self.progress_slider)
        
        # Time Labels
        time_layout = QHBoxLayout()
        self.current_time_label = QLabel("00:00")
        self.total_time_label = QLabel("00:00")
        time_layout.addWidget(self.current_time_label)
        time_layout.addStretch()
        time_layout.addWidget(self.total_time_label)
        layout.addLayout(time_layout)
        
        # Settings
        self.autoplay_checkbox = QCheckBox("Autoplay next item in list")
        layout.addWidget(self.autoplay_checkbox)

        self.remote_mode_checkbox = QCheckBox("Remote Mode (Left/Right instead of Up/Down)")
        self.remote_mode_checkbox.stateChanged.connect(self.update_shortcuts)
        self.remote_mode_checkbox.setChecked(True)
        layout.addWidget(self.remote_mode_checkbox)
        
        # Logo Settings
        logo_layout = QHBoxLayout()
        self.logo_checkbox = QCheckBox("Enable Logo for audio tracks")
        self.logo_checkbox.setChecked(True)
        self.logo_checkbox.stateChanged.connect(self.update_logo_visibility)
        
        self.logo_btn = QPushButton("Select Logo Image")
        self.logo_btn.clicked.connect(self.select_logo)
        
        logo_layout.addWidget(self.logo_checkbox)
        logo_layout.addWidget(self.logo_btn)
        layout.addLayout(logo_layout)
        
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.check_player_status)
        self.status_timer.start(500)
        
        # Master Volume
        vol_layout = QHBoxLayout()
        vol_layout.addWidget(QLabel("Master Volume:"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.volume_slider.setTickInterval(10)
        self.volume_slider.valueChanged.connect(self.set_volume)
        vol_layout.addWidget(self.volume_slider)
        layout.addLayout(vol_layout)
        
        central_widget.setLayout(layout)
        
        # Keyboard Shortcuts
        self.shortcut_space = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        self.shortcut_space.activated.connect(self.toggle_play_pause)
        
        self.shortcut_enter = QShortcut(QKeySequence(Qt.Key.Key_Return), self.playlist)
        self.shortcut_enter.activated.connect(self.play_media)
        
        self.shortcut_enter2 = QShortcut(QKeySequence(Qt.Key.Key_Enter), self.playlist)
        self.shortcut_enter2.activated.connect(self.play_media)
        
        self.shortcut_delete = QShortcut(QKeySequence(Qt.Key.Key_Delete), self.playlist)
        self.shortcut_delete.activated.connect(self.remove_file)
        
        self.shortcut_prev = QShortcut(QKeySequence(Qt.Key.Key_Up), self)
        self.shortcut_prev.activated.connect(self.play_previous_file)
        
        self.shortcut_next = QShortcut(QKeySequence(Qt.Key.Key_Down), self)
        self.shortcut_next.activated.connect(self.play_next_file)

        # Function Keys
        self.f4_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F4), self)
        self.f4_shortcut.activated.connect(self.play_media)

        self.f5_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F5), self)
        self.f5_shortcut.activated.connect(self.stop_media)

        self.f6_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F6), self)
        self.f6_shortcut.activated.connect(self.play_previous_file)

        self.f7_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F7), self)
        self.f7_shortcut.activated.connect(self.play_next_file)

        self.f8_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F8), self)
        self.f8_shortcut.activated.connect(self.fade_out)

        self.f9_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F9), self)
        self.f9_shortcut.activated.connect(self.toggle_projection_fullscreen)

        self.f11_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F11), self)
        self.f11_shortcut.activated.connect(lambda: self.logo_overlay_btn.animateClick())

        self.f12_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F12), self)
        self.f12_shortcut.activated.connect(self.save_project)

        self.update_shortcuts()

    def update_shortcuts(self):
        if not hasattr(self, 'shortcut_prev') or not hasattr(self, 'shortcut_next'):
            return
            
        if self.remote_mode_checkbox.isChecked():
            self.shortcut_prev.setKey(QKeySequence(Qt.Key.Key_Left))
            self.shortcut_next.setKey(QKeySequence(Qt.Key.Key_Right))
        else:
            self.shortcut_prev.setKey(QKeySequence(Qt.Key.Key_Up))
            self.shortcut_next.setKey(QKeySequence(Qt.Key.Key_Down))
        
    def select_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Logo Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*.*)"
        )
        if file_path:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.projection_window.visualizer.logo_pixmap = pixmap
                QMessageBox.information(self, "Logo Loaded", "Visualization logo has been successfully loaded.")
            else:
                QMessageBox.warning(self, "Error", "Failed to load the image file.")
                
    def update_logo_visibility(self):
        self.projection_window.visualizer.show_logo = self.logo_checkbox.isChecked()

    def add_files(self):
        try:
            files, _ = QFileDialog.getOpenFileNames(
                self, 
                "Select Media Files", 
                "", 
                "Media (*.mp4 *.mp3 *.mkv *.jpg *.png *.wav *.flac);;All Files (*.*)"
            )
            for file in files:
                self.playlist.addItem(file)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"A problem occurred while adding files:\n{e}")

    def remove_file(self):
        selected_items = self.playlist.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            self.playlist.takeItem(self.playlist.row(item))

    def format_time(self, ms):
        s, ms = divmod(ms, 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        else:
            return f"{m:02d}:{s:02d}"

    def slider_pressed(self):
        self.user_is_seeking = True

    def slider_released(self):
        self.user_is_seeking = False
        self.media_player.set_position(self.progress_slider.value() / 1000.0)

    def set_position(self, value):
        total_time = self.media_player.get_length()
        if total_time > 0:
            current_ms = int((value / 1000.0) * total_time)
            self.current_time_label.setText(self.format_time(current_ms))

    def check_player_status(self):
        if getattr(self, 'is_playing', False):
            if not getattr(self, 'is_transitioning', False):
                state = self.media_player.get_state()
                if state in (vlc.State.Ended, vlc.State.Stopped):
                    self.is_playing = False
                    if state == vlc.State.Ended and getattr(self, 'autoplay_checkbox', None) and self.autoplay_checkbox.isChecked():
                        self.play_next_file()
            
            if not self.user_is_seeking:
                pos = self.media_player.get_position()
                if pos >= 0:
                    self.progress_slider.setValue(int(pos * 1000))
                
                curr_time = self.media_player.get_time()
                total_time = self.media_player.get_length()
                if curr_time >= 0:
                    self.current_time_label.setText(self.format_time(curr_time))
                if total_time >= 0:
                    self.total_time_label.setText(self.format_time(total_time))
        else:
            if not self.user_is_seeking:
                self.progress_slider.setValue(0)
                self.current_time_label.setText("00:00")
                self.total_time_label.setText("00:00")

    def play_next_file(self):
        current_row = self.playlist.currentRow()
        if current_row < self.playlist.count() - 1:
            self.playlist.setCurrentRow(current_row + 1)
            self.play_media()

    def play_previous_file(self):
        current_row = self.playlist.currentRow()
        if current_row > 0:
            self.playlist.setCurrentRow(current_row - 1)
            self.play_media()

    def save_project(self):
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                "Save Project", 
                "", 
                "Project Files (*.json);;All Files (*.*)"
            )
            if file_path:
                items = [self.playlist.item(i).text() for i in range(self.playlist.count())]
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(items, f, ensure_ascii=False, indent=4)
                QMessageBox.information(self, "Saved", "Project has been saved successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save project:\n{e}")

    def load_project(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Load Project",
                "",
                "Project Files (*.json);;All Files (*.*)"
            )
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    items = json.load(f)
                self.playlist.clear()
                self.playlist.addItems(items)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load project:\n{e}")

    def play_media(self):
        selected_item = self.playlist.currentItem()
        if not selected_item:
            return
            
        file_path = selected_item.text()
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Error", "Invalid file path. Selected file does not exist.")
            return
            
        if getattr(self, 'is_transitioning', False):
            return
            
        if getattr(self, 'logo_overlay_btn', None) and self.logo_overlay_btn.isChecked():
            self.projection_window.set_mode_audio()
        else:
            is_audio_only = file_path.lower().endswith(('.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'))
            if is_audio_only:
                self.projection_window.set_mode_audio()
            else:
                self.projection_window.set_mode_video()
            
        threading.Thread(target=self._play_transition_thread, args=(file_path,), daemon=True).start()

    def _play_transition_thread(self, file_path):
        self.is_transitioning = True
        target_volume = self.volume_slider.value()
        
        try:
            if self.is_playing:
                current_volume = self.media_player.audio_get_volume()
                if current_volume < 0:
                    current_volume = target_volume
                    
                steps_out = 20
                sleep_interval_out = 1.0 / steps_out
                step_volume_out = current_volume / steps_out
                step_brightness_out = 1.0 / steps_out
                current_brightness = 1.0
                
                for _ in range(steps_out):
                    current_volume -= step_volume_out
                    current_brightness -= step_brightness_out
                    
                    if current_volume < 0:
                        current_volume = 0
                    if current_brightness < 0:
                        current_brightness = 0.0
                        
                    self.media_player.audio_set_volume(int(current_volume))
                    self.media_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, float(current_brightness))
                    self.projection_window.visualizer.volume_multiplier = float(current_volume) / 100.0
                    time.sleep(sleep_interval_out)
                    
                self.media_player.stop()
                self.media_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, 0.0)
                
            media = self.vlc_instance.media_new(file_path)
            self.media_player.set_media(media)
            self.media_player.play()
            self.is_playing = True
            
            time.sleep(0.15)
            self.media_player.audio_set_volume(0)
            self.media_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, 0.0)
            self.media_player.video_set_adjust_int(vlc.VideoAdjustOption.Enable, 1) 
            
            steps_in = 20
            sleep_interval_in = 0.3 / steps_in
            current_volume_in = 0
            step_volume_in = target_volume / steps_in
            current_brightness_in = 0.0
            step_brightness_in = 1.0 / steps_in
            
            for _ in range(steps_in):
                current_volume_in += step_volume_in
                current_brightness_in += step_brightness_in
                
                if current_volume_in > target_volume:
                    current_volume_in = target_volume
                if current_brightness_in > 1.0:
                    current_brightness_in = 1.0
                    
                self.media_player.audio_set_volume(int(current_volume_in))
                self.media_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, float(current_brightness_in))
                self.projection_window.visualizer.volume_multiplier = float(current_volume_in) / 100.0
                time.sleep(sleep_interval_in)
                
            self.media_player.audio_set_volume(target_volume)
            self.media_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, 1.0)
            self.projection_window.visualizer.volume_multiplier = float(target_volume) / 100.0
            
        except Exception as e:
            print(f"Transition error: {e}")
            
        self.is_transitioning = False

    def toggle_play_pause(self):
        if self.is_playing:
            state = self.media_player.get_state()
            if state == vlc.State.Playing:
                self.media_player.pause()
            else:
                self.media_player.play()
        else:
            self.play_media()

    def stop_media(self):
        try:
            self.media_player.stop()
            self.is_playing = False
        except Exception as e:
            print(f"Stop error: {e}")

    def fade_out(self):
        if not self.is_playing or getattr(self, 'is_transitioning', False):
            return
            
        threading.Thread(target=self._fade_out_thread, daemon=True).start()
        
    def _fade_out_thread(self):
        self.is_transitioning = True
        steps = 40
        sleep_interval = 2.0 / steps
        
        current_volume = self.media_player.audio_get_volume()
        if current_volume < 0:
            current_volume = self.volume_slider.value()
            
        if current_volume <= 0:
            self.stop_media()
            self.is_transitioning = False
            return

        step_volume = current_volume / steps
        current_brightness = 1.0
        step_brightness = 1.0 / steps
        
        for _ in range(steps):
            current_volume -= step_volume
            current_brightness -= step_brightness
            
            if current_volume < 0:
                current_volume = 0
            if current_brightness < 0:
                current_brightness = 0.0
                
            self.media_player.audio_set_volume(int(current_volume))
            self.media_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, float(current_brightness))
            self.projection_window.visualizer.volume_multiplier = float(current_volume) / 100.0
            time.sleep(sleep_interval)
            
        self.stop_media()
        self.media_player.audio_set_volume(self.volume_slider.value())
        self.media_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, 1.0)
        self.is_transitioning = False

    def toggle_projection_fullscreen(self):
        if self.projection_window.isFullScreen():
            self.projection_window.showNormal()
        else:
            self.projection_window.showFullScreen()
        
        self.activateWindow()
        self.raise_()

    def toggle_projection_window(self):
        if self.projection_window.isVisible():
            self.projection_window.hide()
            self.window_btn.setText("Show Projection Window")
        else:
            self.projection_window.show()
            self.window_btn.setText("Hide Projection Window")

    def toggle_logo_overlay(self, checked):
        if checked:
            self.projection_window.set_mode_audio()
        else:
            selected_item = self.playlist.currentItem()
            if selected_item:
                file_path = selected_item.text()
                is_audio_only = file_path.lower().endswith(('.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'))
                if is_audio_only:
                    self.projection_window.set_mode_audio()
                else:
                    self.projection_window.set_mode_video()
            else:
                self.projection_window.set_mode_video()

    def set_volume(self, value):
        try:
            self.media_player.audio_set_volume(value)
            self.projection_window.visualizer.volume_multiplier = value / 100.0
        except Exception:
            pass

    def closeEvent(self, event):
        self.projection_window.close()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # VS Code Dark Theme Stylesheet
    app.setStyleSheet("""
        QMainWindow, QWidget {
            background-color: #1e1e1e;
            color: #d4d4d4;
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            font-size: 10pt;
        }
        
        QPushButton {
            background-color: #333333;
            border: 1px solid #454545;
            color: #cccccc;
            padding: 6px 12px;
            border-radius: 2px;
            min-height: 18px;
        }
        QPushButton:hover {
            background-color: #454545;
        }
        QPushButton:pressed {
            background-color: #007acc;
            color: white;
            border: 1px solid #007acc;
        }
        QPushButton:checked {
            background-color: #0e639c;
            color: white;
        }
        
        QListWidget {
            background-color: #252526;
            border: 1px solid #3c3c3c;
            color: #cccccc;
            outline: none;
            padding: 2px;
        }
        QListWidget::item {
            padding: 6px;
            border-bottom: 1px solid #2d2d2d;
        }
        QListWidget::item:selected {
            background-color: #37373d;
            color: #ffffff;
            border-left: 3px solid #007acc;
        }
        QListWidget::item:hover {
            background-color: #2a2d2e;
        }
        
        QSlider::groove:horizontal {
            border: 1px solid #3c3c3c;
            height: 4px;
            background: #3c3c3c;
            margin: 2px 0;
        }
        QSlider::handle:horizontal {
            background: #007acc;
            width: 14px;
            height: 14px;
            margin: -5px 0;
            border-radius: 7px;
        }
        QSlider::handle:horizontal:hover {
            background: #1c97ea;
        }
        
        QCheckBox {
            spacing: 8px;
        }
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            background-color: #3c3c3c;
            border: 1px solid #454545;
            border-radius: 2px;
        }
        QCheckBox::indicator:checked {
            background-color: #007acc;
            border: 1px solid #007acc;
            image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiIHdpZHRoPSIxMnB4IiBoZWlnaHQ9IjEycHgiPjxwYXRoIGQ9Ik05IDE2LjE3TDQuODMgMTJsLTEuNDEgMS40MUw5IDE5IDIxIDdsLTEuNDEtMS40MXoiLz48L3N2Zz4=);
        }
        
        QLabel {
            color: #bbbbbb;
        }
        
        QScrollBar:vertical {
            border: none;
            background: #1e1e1e;
            width: 12px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background: #424242;
            min-height: 20px;
            border-radius: 0px;
            margin: 2px;
        }
        QScrollBar::handle:vertical:hover {
            background: #4f4f4f;
        }
        QScrollBar::add-line, QScrollBar::sub-line {
            height: 0px;
        }
    """)
    
    window = App()
    window.show()
    sys.exit(app.exec())