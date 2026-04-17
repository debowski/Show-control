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

try:
    import vlc
except ImportError:
    print("Błąd: Biblioteka python-vlc nie jest zainstalowana.")
    print("Zainstaluj ją używając: pip install python-vlc")
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
        
        # Rysowanie tła (logo)
        if self.show_logo and getattr(self, 'logo_pixmap', None) and not self.logo_pixmap.isNull():
            target_h = int(h * 0.8)
            target_w = int(w * 0.8)
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
        # Zwykłe okno, aby móc przenosić i skalować materiał po wyjściu z pełnego ekranu
        self.setWindowFlags(Qt.WindowType.Window)
        self.setWindowTitle("Projekcja - Odtwarzacz")
        self.setStyleSheet("background-color: black;")
        
        self.video_widget = QWidget()
        self.video_widget.setStyleSheet("background-color: black;")
        
        self.vis_container = QWidget()
        self.vis_container.setStyleSheet("background-color: black;")
        vis_layout = QVBoxLayout(self.vis_container)
        vis_layout.setContentsMargins(0, 0, 0, 0)
        self.visualizer = AudioVisualizer()
        # Wizualizer wypełnia całościowo swój kontener, by poprawnie wyśrodkować logo na pulpicie
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
        # Domyślnie otwiera się na drugim monitorze (jeśli dostępny)
        screens = QApplication.screens()
        if len(screens) > 1:
            second_screen = screens[1]
            self.resize(800, 600)
            self.move(second_screen.geometry().topLeft() + second_screen.geometry().center() - self.rect().center())
            self.showFullScreen()
        else:
            # Okno pomocnicze na głównym ekranie, jeśli brak drugiego monitora
            self.setWindowTitle("Projekcja")
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
        self.setWindowTitle("Show Control - Operator")
        self.setGeometry(100, 100, 600, 400)
        
        # Inicjalizacja VLC z obsługą wyjątków na wypadek braku odpowiednich bibliotek
        try:
            # Używamy Direct3D9 zamiast domyślnego D3D11, aby uniknąć błędów wyjścia obrazu w PyQt 
            # oraz '--quiet', by ukryć niegroźne logi dekodera z konsoli
            self.vlc_instance = vlc.Instance('--no-xlib', '--quiet', '--vout=direct3d9', '--video-filter=adjust')
            self.media_player = self.vlc_instance.media_player_new()
            # Włączamy filtr adjust dla płynnych przejść jasności obrazu
            self.media_player.video_set_adjust_int(vlc.VideoAdjustOption.Enable, 1)
        except Exception as e:
            QMessageBox.critical(self, "Błąd VLC", f"Nie można zainicjować silnika VLC:\n{e}\nUpewnij się, że VLC media player jest poprawnie zainstalowany.")
            sys.exit(1)
            
        # Utworzenie okna projekcyjnego i przeniesienie na 2. ekran
        self.projection_window = ProjectionWindow()
        self.projection_window.move_to_second_screen()
        self.projection_window.show()
        
        # Podłączenie instancji odtwarzacza do Okna Projekcyjnego (zależne od OS)
        if sys.platform.startswith("win"):
            self.media_player.set_hwnd(int(self.projection_window.video_widget.winId()))
        elif sys.platform.startswith("linux"):
            self.media_player.set_xwindow(int(self.projection_window.video_widget.winId()))
        elif sys.platform == "darwin":
            self.media_player.set_nsobject(int(self.projection_window.video_widget.winId()))
            
        # Przekaż wejście myszy i klawiatury do okna nadrzędnego, co pozwala na obsługę np. dwukliku
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
        
        # Lista odtwarzania do zarządzania materiałami
        self.playlist = PlaylistWidget()
        self.playlist.itemDoubleClicked.connect(lambda item: self.play_media())
        layout.addWidget(self.playlist)
        
        # Przyciski zarządzania projektem
        project_btn_layout = QHBoxLayout()
        
        self.save_proj_btn = QPushButton("Zapisz projekt")
        self.save_proj_btn.clicked.connect(self.save_project)
        project_btn_layout.addWidget(self.save_proj_btn)
        
        self.load_proj_btn = QPushButton("Wczytaj projekt")
        self.load_proj_btn.clicked.connect(self.load_project)
        project_btn_layout.addWidget(self.load_proj_btn)
        
        layout.addLayout(project_btn_layout)
        
        # Układ przycisków sterowania
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Dodaj")
        self.add_btn.clicked.connect(self.add_files)
        btn_layout.addWidget(self.add_btn)
        
        self.remove_btn = QPushButton("Usuń")
        self.remove_btn.clicked.connect(self.remove_file)
        btn_layout.addWidget(self.remove_btn)
        
        self.play_btn = QPushButton("Play")
        self.play_btn.clicked.connect(self.play_media)
        btn_layout.addWidget(self.play_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_media)
        btn_layout.addWidget(self.stop_btn)
        
        self.fade_btn = QPushButton("Fade Out")
        self.fade_btn.clicked.connect(self.fade_out)
        btn_layout.addWidget(self.fade_btn)
        
        self.fullscreen_btn = QPushButton("Pełny Ekran")
        self.fullscreen_btn.clicked.connect(self.toggle_projection_fullscreen)
        btn_layout.addWidget(self.fullscreen_btn)
        
        self.window_btn = QPushButton("Ukryj okno projekcji")
        self.window_btn.clicked.connect(self.toggle_projection_window)
        btn_layout.addWidget(self.window_btn)
        
        self.logo_overlay_btn = QPushButton("Logo Overlay")
        self.logo_overlay_btn.setCheckable(True)
        self.logo_overlay_btn.clicked.connect(self.toggle_logo_overlay)
        btn_layout.addWidget(self.logo_overlay_btn)
        
        layout.addLayout(btn_layout)

        # Pasek postępu
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.sliderMoved.connect(self.set_position)
        self.progress_slider.sliderPressed.connect(self.slider_pressed)
        self.progress_slider.sliderReleased.connect(self.slider_released)
        layout.addWidget(self.progress_slider)
        
        # Etykiety czasu
        time_layout = QHBoxLayout()
        self.current_time_label = QLabel("00:00")
        self.total_time_label = QLabel("00:00")
        time_layout.addWidget(self.current_time_label)
        time_layout.addStretch()
        time_layout.addWidget(self.total_time_label)
        layout.addLayout(time_layout)
        
        # Opcja autoodtwarzania (autoplay)
        self.autoplay_checkbox = QCheckBox("Autoodtwarzanie kolejnych plików z listy")
        layout.addWidget(self.autoplay_checkbox)
        
        # Opcja logo dla audio
        self.vis_checkbox = QCheckBox("Pokaż logo dla plików audio")
        self.vis_checkbox.setChecked(True)
        layout.addWidget(self.vis_checkbox)
        
        # Opcje logo
        logo_layout = QHBoxLayout()
        self.logo_checkbox = QCheckBox("Wyświetlaj logo pod wizualizacją")
        self.logo_checkbox.setChecked(True)
        self.logo_checkbox.stateChanged.connect(self.update_logo_visibility)
        
        self.logo_btn = QPushButton("Wybierz plik logo")
        self.logo_btn.clicked.connect(self.select_logo)
        
        logo_layout.addWidget(self.logo_checkbox)
        logo_layout.addWidget(self.logo_btn)
        layout.addLayout(logo_layout)
        
        # Timer do nasłuchiwania czy materiał wideo dotarł do końca (Ended)
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.check_player_status)
        self.status_timer.start(500)
        
        # Suwak głośności dla operatora
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.volume_slider.setTickInterval(10)
        self.volume_slider.valueChanged.connect(self.set_volume)
        layout.addWidget(self.volume_slider)
        
        central_widget.setLayout(layout)
        
        # Bindowanie klawisza "Spacja" jako uniwersalny klawisz skrótu Play/Pause
        self.shortcut_space = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        self.shortcut_space.activated.connect(self.toggle_play_pause)
        
        # Bindowanie klawisza "Enter" do uruchamiania odtwarzania zaznaczonego elementu
        self.shortcut_enter = QShortcut(QKeySequence(Qt.Key.Key_Return), self.playlist)
        self.shortcut_enter.activated.connect(self.play_media)
        
        self.shortcut_enter2 = QShortcut(QKeySequence(Qt.Key.Key_Enter), self.playlist)
        self.shortcut_enter2.activated.connect(self.play_media)
        
        # Bindowanie klawisza "Delete" do usuwania plików
        self.shortcut_delete = QShortcut(QKeySequence(Qt.Key.Key_Delete), self.playlist)
        self.shortcut_delete.activated.connect(self.remove_file)
        
        # Bindowanie strzałek (Góra/Dół) do przełączania materiałów na liście
        self.shortcut_up = QShortcut(QKeySequence(Qt.Key.Key_Up), self)
        self.shortcut_up.activated.connect(self.play_previous_file)
        
        self.shortcut_down = QShortcut(QKeySequence(Qt.Key.Key_Down), self)
        self.shortcut_down.activated.connect(self.play_next_file)
        
    def select_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Wybierz plik graficzny (logo)",
            "",
            "Obrazy (*.png *.jpg *.jpeg *.bmp *.gif);;Wszystkie pliki (*.*)"
        )
        if file_path:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.projection_window.visualizer.logo_pixmap = pixmap
                QMessageBox.information(self, "Zalogowano", "Pomyślnie wczytano logo do wizualizacji.")
            else:
                QMessageBox.warning(self, "Błąd", "Nie udało się wczytać pliku jako obraz.")
                
    def update_logo_visibility(self):
        self.projection_window.visualizer.show_logo = self.logo_checkbox.isChecked()

    def add_files(self):
        # Otwórz okno QFileDialog aby dodać pliki .mp4, .mp3, .mkv do czytelnej listy
        try:
            files, _ = QFileDialog.getOpenFileNames(
                self, 
                "Wybierz pliki multimedialne", 
                "", 
                "Multimedia (*.mp4 *.mp3 *.mkv *.jpg *.png);;Wszystkie pliki (*.*)"
            )
            for file in files:
                self.playlist.addItem(file)
        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Wystąpił problem podczas dodawania plików:\n{e}")

    def remove_file(self):
        # Usuwanie zaznaczonych elementów z listy
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
        # Aktualizacja etykiety czasu podczas przesuwania
        total_time = self.media_player.get_length()
        if total_time > 0:
            current_ms = int((value / 1000.0) * total_time)
            self.current_time_label.setText(self.format_time(current_ms))

    def check_player_status(self):
        # Sprawdzanie czy plik naturalnie dobrnął do końca, bez wycięć przez przejścia
        if getattr(self, 'is_playing', False):
            if not getattr(self, 'is_transitioning', False):
                state = self.media_player.get_state()
                if state in (vlc.State.Ended, vlc.State.Stopped):
                    self.is_playing = False
                    if state == vlc.State.Ended and getattr(self, 'autoplay_checkbox', None) and self.autoplay_checkbox.isChecked():
                        self.play_next_file()
            
            # Aktualizacja suwaka postępu i czasu
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
                "Zapisz projekt", 
                "", 
                "Plik projektu (*.json);;Wszystkie pliki (*.*)"
            )
            if file_path:
                items = [self.playlist.item(i).text() for i in range(self.playlist.count())]
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(items, f, ensure_ascii=False, indent=4)
                QMessageBox.information(self, "Zapisano", "Projekt został pomyślnie zapisany.")
        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Nie udało się zapisać projektu:\n{e}")

    def load_project(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Wczytaj projekt",
                "",
                "Plik projektu (*.json);;Wszystkie pliki (*.*)"
            )
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    items = json.load(f)
                self.playlist.clear()
                self.playlist.addItems(items)
        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Nie udało się wczytać projektu:\n{e}")

    def play_media(self):
        # Uruchamianie zaznaczonego elementu z listy
        selected_item = self.playlist.currentItem()
        if not selected_item:
            return
            
        file_path = selected_item.text()
        
        # Zabezpieczenie na wypadek nieistniejącej lub błędnej ścieżki
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Błąd", "Błędna ścieżka do pliku. Wybrany plik nie istnieje.")
            return
            
        if getattr(self, 'is_transitioning', False):
            return
            
        # Przestawienie trybu w GUI (Zawsze w głównym wątku!)
        if getattr(self, 'logo_overlay_btn', None) and self.logo_overlay_btn.isChecked():
            self.projection_window.set_mode_audio()
        else:
            is_audio_only = file_path.lower().endswith(('.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'))
            if getattr(self, 'vis_checkbox', None) and self.vis_checkbox.isChecked() and is_audio_only:
                self.projection_window.set_mode_audio()
            else:
                self.projection_window.set_mode_video()
            
        # Płynne przejście uruchamiane w osobnym wątku
        threading.Thread(target=self._play_transition_thread, args=(file_path,), daemon=True).start()

    def _play_transition_thread(self, file_path):
        self.is_transitioning = True
        target_volume = self.volume_slider.value()
        
        try:
            # Fade out jeśli coś już gra
            if self.is_playing:
                current_volume = self.media_player.audio_get_volume()
                if current_volume < 0:
                    current_volume = target_volume
                    
                # 1 sekunda fade-out
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
                # Zapobiegawczo upewniamy się, że obraz jest wygaszony przed załadowaniem nowego pliku
                self.media_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, 0.0)
                
            # Uruchomienie nowego pliku
            media = self.vlc_instance.media_new(file_path)
            self.media_player.set_media(media)
            self.media_player.play()
            self.is_playing = True
            
            # Poczekaj chwilę, żeby VLC zdążył rozpocząć odtwarzanie i zaaplikować poziom głośności
            time.sleep(0.15)
            self.media_player.audio_set_volume(0)
            self.media_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, 0.0)
            # Upewniamy się raz jeszcze że filtr działa po załadowaniu nowych mediów
            self.media_player.video_set_adjust_int(vlc.VideoAdjustOption.Enable, 1) 
            
            # Fade in (0.3 sekundy)
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
            print(f"Błąd podczas zmiany pliku z przejściem: {e}")
            
        self.is_transitioning = False

    def toggle_play_pause(self):
        # Metoda dla powiązania spacji - decyduje co zrobić w zalezności czy aktualnie gramy czy nie
        if self.is_playing:
            state = self.media_player.get_state()
            if state == vlc.State.Playing:
                self.media_player.pause()
            else:
                self.media_player.play()
        else:
            # W przypadku spacji i nie-odgrywania - po prostu odpal zaznaczony klip domyślny Play
            self.play_media()

    def stop_media(self):
        # Try..except aby zapobiec wyjątkowi przy zatrzymywaniu gdy player nie jest poprawnie aktywowany
        try:
            self.media_player.stop()
            self.is_playing = False
        except Exception as e:
            print(f"Błąd zatrzymywania: {e}")

    def fade_out(self):
        if not self.is_playing or getattr(self, 'is_transitioning', False):
            return
            
        # Płynne zmniejszanie głośności - uruchamiamy w nowym wątku (threading) aby nie zamrozić GUI
        threading.Thread(target=self._fade_out_thread, daemon=True).start()
        
    def _fade_out_thread(self):
        self.is_transitioning = True
        # Efekt Fade Out z ok. 100 do 0 w 2 sekundy (wykonasz 40 pętli po 0.05 sekundy co = 2.0 sek)
        steps = 40
        sleep_interval = 2.0 / steps
        
        # Upewniamy się, z jakiego poziomu ściszamy - jeśli vlc zwróci -1 bierzemy z suwaka volumingu okna GUI
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
            
        # Gdy głośność w wątku dojdzie do zera zatrzymujemy materiał
        self.stop_media()
        
        # Przywracamy poziom głośności gracza multimedialnego do stanu nominalnego z panelu po stop
        self.media_player.audio_set_volume(self.volume_slider.value())
        self.media_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, 1.0)
        self.is_transitioning = False

    def toggle_projection_fullscreen(self):
        if self.projection_window.isFullScreen():
            self.projection_window.showNormal()
        else:
            self.projection_window.showFullScreen()

    def toggle_projection_window(self):
        if self.projection_window.isVisible():
            self.projection_window.hide()
            self.window_btn.setText("Pokaż okno projekcji")
        else:
            self.projection_window.show()
            self.window_btn.setText("Ukryj okno projekcji")

    def toggle_logo_overlay(self, checked):
        if checked:
            self.projection_window.set_mode_audio()
        else:
            # Przywróć tryb w zależności od aktualnie odtwarzanego pliku
            selected_item = self.playlist.currentItem()
            if selected_item:
                file_path = selected_item.text()
                is_audio_only = file_path.lower().endswith(('.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'))
                if is_audio_only and getattr(self, 'vis_checkbox', None) and self.vis_checkbox.isChecked():
                    self.projection_window.set_mode_audio()
                else:
                    self.projection_window.set_mode_video()
            else:
                self.projection_window.set_mode_video()

    def set_volume(self, value):
        # Metoda dla manipulacji głośnością w locie po ruszeniu suwakiem
        try:
            self.media_player.audio_set_volume(value)
            self.projection_window.visualizer.volume_multiplier = value / 100.0
        except Exception:
            pass

    def closeEvent(self, event):
        # Zamykanie okna projekcyjnego jeżeli operator zamknie główne okno nawigacji
        self.projection_window.close()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())