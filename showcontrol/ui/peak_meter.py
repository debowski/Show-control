"""Miernik Szczytowy Stereo (IEC dBFS) dla konsoli operatora.

Standard IEC 60268-10 / IEC 60268-18 (dBFS):
- Skala: 0 dBFS (Full Scale) do -60 dBFS
- Kolory: zielony (< -18 dBFS), żółty (-18 do -6 dBFS), czerwony (>= -6 dBFS)
- Dwa niezależne kanały stereo: L i R
- Wskaźniki wartości szczytowej (Peak Hold) z czasem powrotu IEC
"""

import time

from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QSizePolicy, QWidget

# Parametry skali IEC dBFS
MIN_DBFS = -60.0
MAX_DBFS = 0.0

# Granice stref kolorystycznych IEC
YELLOW_THRESHOLD_DB = -18.0
RED_THRESHOLD_DB = -6.0

# Dynamika IEC (powrót: ok. 1.7s na 20 dB, spadek szczytu po 1.2s zatrzymania)
DECAY_RATE_DB_PER_SEC = 20.0 / 1.7  # ~11.76 dB/s
PEAK_HOLD_TIME_SEC = 1.2
PEAK_HOLD_DECAY_RATE = 20.0  # 20 dB/s po wygaśnięciu hold


class StereoPeakMeter(QWidget):
    """Widżet pionowego stereofonicznego miernika szczytowego IEC dBFS."""

    peak_changed = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Stała szerokość, wysokość rozciąga się tak jak suwaki obok, żeby
        # skala miernika pokrywała się z długością suwaków głośności i jasności.
        self.setFixedWidth(68)
        self.setMinimumHeight(140)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        # Poziomy chwilowe (w dBFS)
        self._current_l = MIN_DBFS
        self._current_r = MIN_DBFS

        # Poziomy Peak Hold (w dBFS)
        self._peak_hold_l = MIN_DBFS
        self._peak_hold_r = MIN_DBFS
        self._peak_hold_time_l = 0.0
        self._peak_hold_time_r = 0.0

        # Czas ostatniej klatki animacji
        self._last_tick = time.time()

        # Brak pomiaru: sesja gra, a danych nie ma. Nie jest to cisza.
        self._no_measurement = False

        # Timer do płynnego opadania (decay) i odświeżania (~33 FPS)
        self._timer = QTimer(self)
        self._timer.setInterval(30)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

    def set_levels(self, db_l: float, db_r: float):
        """Ustawia docelowe poziomy szczytowe kanałów L i R (w dBFS)."""
        now = time.time()
        self._no_measurement = False

        # Ograniczenie do zakresu
        db_l = max(MIN_DBFS, min(MAX_DBFS, db_l))
        db_r = max(MIN_DBFS, min(MAX_DBFS, db_r))

        # Atak IEC: natychmiastowy wzrost
        if db_l >= self._current_l:
            self._current_l = db_l
        if db_r >= self._current_r:
            self._current_r = db_r

        # Obsługa Peak Hold L
        if db_l >= self._peak_hold_l:
            self._peak_hold_l = db_l
            self._peak_hold_time_l = now
        # Obsługa Peak Hold R
        if db_r >= self._peak_hold_r:
            self._peak_hold_r = db_r
            self._peak_hold_time_r = now

        highest_peak = max(self._peak_hold_l, self._peak_hold_r)
        self.peak_changed.emit(highest_peak)
        self.update()

    def reset(self):
        """Zeruje wskaźniki do ciszy."""
        self._no_measurement = False
        self._clear_levels()
        self.peak_changed.emit(MIN_DBFS)
        self.update()

    def set_no_measurement(self):
        """Sesja gra, ale miernik nie ma świeżych danych.

        To nie cisza: strumień pomiaru padł albo sygnał idzie na inne
        urządzenie. ADR 0006 zabrania pokazywania tu ciszy.
        """
        self._no_measurement = True
        self._clear_levels()
        self.update()

    def _clear_levels(self):
        """Zeruje słupki i peak hold; wspólne dla ciszy i braku pomiaru."""
        self._current_l = MIN_DBFS
        self._current_r = MIN_DBFS
        self._peak_hold_l = MIN_DBFS
        self._peak_hold_r = MIN_DBFS
        self._last_tick = time.time()

    def _on_tick(self):
        if self._no_measurement:
            return

        now = time.time()
        dt = now - self._last_tick
        self._last_tick = now

        # Opadanie bieżącego poziomu (IEC decay)
        decay = DECAY_RATE_DB_PER_SEC * dt
        self._current_l = max(MIN_DBFS, self._current_l - decay)
        self._current_r = max(MIN_DBFS, self._current_r - decay)

        # Opadanie Peak Hold L po czasie zatrzymania
        if now - self._peak_hold_time_l > PEAK_HOLD_TIME_SEC:
            hold_decay = PEAK_HOLD_DECAY_RATE * dt
            self._peak_hold_l = max(self._current_l, self._peak_hold_l - hold_decay)

        # Opadanie Peak Hold R po czasie zatrzymania
        if now - self._peak_hold_time_r > PEAK_HOLD_TIME_SEC:
            hold_decay = PEAK_HOLD_DECAY_RATE * dt
            self._peak_hold_r = max(self._current_r, self._peak_hold_r - hold_decay)

        highest_peak = max(self._peak_hold_l, self._peak_hold_r)
        self.peak_changed.emit(highest_peak)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        w = self.width()
        h = self.height()

        # Tło modułu miernika
        painter.fillRect(0, 0, w, h, QColor("#141414"))
        painter.setPen(QColor("#2c2c2c"))
        painter.drawRect(0, 0, w - 1, h - 1)

        # Geometria słupków
        bar_top = 4
        bar_bottom = h - 10
        bar_height = bar_bottom - bar_top
        bar_w = 9

        bar_l_x = 6
        bar_r_x = 18
        scale_x = 31

        # Podziałka dBFS (kreski i etykiety)
        ticks = [
            (0, " 0"),
            (-3, "-3"),
            (-6, "-6"),
            (-12, "-12"),
            (-18, "-18"),
            (-24, "-24"),
            (-36, "-36"),
            (-48, "-48"),
        ]

        font = QFont("Consolas", 6)
        painter.setFont(font)

        for db_val, label in ticks:
            frac = (db_val - MIN_DBFS) / (MAX_DBFS - MIN_DBFS)
            y = int(bar_bottom - frac * bar_height)

            # Kolor kreski w zależności od strefy
            if db_val >= RED_THRESHOLD_DB:
                line_color = QColor("#ff4444")
            elif db_val >= YELLOW_THRESHOLD_DB:
                line_color = QColor("#ddaa00")
            else:
                line_color = QColor("#555555")

            painter.setPen(line_color)
            painter.drawLine(scale_x, y, scale_x + 3, y)

            painter.setPen(QColor("#888888"))
            painter.drawText(scale_x + 5, y + 3, label)

        if self._no_measurement:
            # Kratka zamiast słupków: miernik nie wie, co gra. Wyraźnie inne
            # niż cisza, która rysuje zgaszone segmenty (ADR 0006).
            plot_left = bar_l_x
            plot_right = scale_x - 2
            painter.save()
            painter.setClipRect(plot_left, bar_top, plot_right - plot_left, bar_height)
            painter.setPen(QColor("#2a2a2a"))
            for x in range(plot_left - bar_height, plot_right, 9):
                painter.drawLine(x, bar_bottom, x + bar_height, bar_top)
            painter.restore()
            self._draw_channel_labels(painter, h, bar_l_x, bar_r_x)
            return

        # Rysowanie segmentów słupków L i R
        step = 3
        num_segments = bar_height // step

        for seg in range(num_segments):
            y_seg = bar_bottom - (seg + 1) * step
            # Poziom dBFS odpowiadający środkowi tego segmentu
            frac = (num_segments - 1 - seg) / (num_segments - 1) if num_segments > 1 else 0
            seg_db = MIN_DBFS + (1.0 - frac) * (MAX_DBFS - MIN_DBFS)

            # Dobór koloru świecącego i zgaszonego
            if seg_db >= RED_THRESHOLD_DB:
                lit_color = QColor("#ff3333")
                dim_color = QColor("#331010")
            elif seg_db >= YELLOW_THRESHOLD_DB:
                lit_color = QColor("#f1c40f")
                dim_color = QColor("#332b0a")
            else:
                lit_color = QColor("#2ecc71")
                dim_color = QColor("#0d2e18")

            # Kanał L
            color_l = lit_color if seg_db <= self._current_l else dim_color
            painter.fillRect(bar_l_x, y_seg, bar_w, step - 1, color_l)

            # Kanał R
            color_r = lit_color if seg_db <= self._current_r else dim_color
            painter.fillRect(bar_r_x, y_seg, bar_w, step - 1, color_r)

        # Wskaźniki Peak Hold (pozioma kreska 2px)
        self._draw_peak_line(painter, bar_l_x, bar_w, self._peak_hold_l, bar_bottom, bar_height)
        self._draw_peak_line(painter, bar_r_x, bar_w, self._peak_hold_r, bar_bottom, bar_height)

        # Etykiety kanałów "L" i "R" na dole
        self._draw_channel_labels(painter, h, bar_l_x, bar_r_x)

    def _draw_channel_labels(self, painter, height, bar_l_x, bar_r_x):
        label_font = QFont("Arial", 6, QFont.Weight.Bold)
        painter.setFont(label_font)
        painter.setPen(QColor("#aaaaaa"))
        painter.drawText(bar_l_x + 1, height - 1, "L")
        painter.drawText(bar_r_x + 1, height - 1, "R")

    def _draw_peak_line(self, painter, x, width, db_val, bar_bottom, bar_height):
        if db_val <= MIN_DBFS:
            return
        frac = (db_val - MIN_DBFS) / (MAX_DBFS - MIN_DBFS)
        y = int(bar_bottom - frac * bar_height)

        if db_val >= RED_THRESHOLD_DB:
            color = QColor("#ffffff")
        elif db_val >= YELLOW_THRESHOLD_DB:
            color = QColor("#ffffff")
        else:
            color = QColor("#ddffdd")

        pen = QPen(color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawLine(x, y, x + width - 1, y)
