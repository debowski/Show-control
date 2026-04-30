import subprocess
import threading
import queue
import os

from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont

try:
    from mutagen import File as MutagenFile
except ImportError:
    MutagenFile = None


class PlaylistTable(QTableWidget):
    duration_updated = pyqtSignal(int, str)

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

        self.playing_row = -1
        self.duration_updated.connect(self.on_duration_updated)

        # --- kolejka + worker ---
        self._queue = queue.Queue()
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()

    # =========================
    # PUBLIC
    # =========================
    def add_file(self, file_path, vlc_instance=None):
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

        # wrzucamy do kolejki zamiast tworzyć nowe wątki
        self._queue.put((file_path, row))

    # =========================
    # WORKER
    # =========================
    def _worker(self):
        while True:
            path, row = self._queue.get()
            try:
                duration = self._get_duration_ffprobe(path)

                # fallback dla audio (jeśli ffprobe nie działa)
                if duration is None and MutagenFile:
                    duration = self._get_duration_mutagen(path)

                if duration:
                    time_str = self._format_time(duration)
                    self.duration_updated.emit(row, time_str)
            except Exception:
                pass
            finally:
                self._queue.task_done()

    # =========================
    # FFPROBE
    # =========================
    def _get_duration_ffprobe(self, path):
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                path
            ]

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=2
            )

            if result.returncode == 0:
                value = result.stdout.strip()
                if value:
                    return float(value)
        except Exception:
            return None

        return None

    # =========================
    # MUTAGEN (fallback audio)
    # =========================
    def _get_duration_mutagen(self, path):
        try:
            audio = MutagenFile(path)
            if audio and audio.info:
                return audio.info.length
        except Exception:
            pass
        return None

    # =========================
    # UI UPDATE
    # =========================
    def on_duration_updated(self, row, time_str):
        if row < self.rowCount():
            item = self.item(row, 1)
            if item:
                item.setText(time_str)

    # =========================
    # FORMAT
    # =========================
    def _format_time(self, seconds):
        seconds = int(seconds)
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

    # =========================
    # HIGHLIGHT
    # =========================
    def set_playing_row(self, row):
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