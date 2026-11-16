"""Analizator widma audio (20 Hz - 20 kHz) dla konsoli operatora.

Przedstawia aktualne widmo częstotliwości:
- Zakres: 20 Hz - 20 kHz w skali logarytmicznej
- 24 pasma częstotliwościowe z oznaczeniami
- Płynne animowanie poziomów (szybki atak, grawitacyjne opadanie IEC)
- Wskaźniki szczytów (Peak Hold) dla każdego pasma
- Segmentowy styl LED spójny z miernikiem szczytowym IEC
"""

import math
import random
import time

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QWidget

# Zakres częstotliwości
FREQ_MIN_HZ = 20.0
FREQ_MAX_HZ = 20000.0
NUM_BANDS = 24

# Poziomy w dBFS
MIN_DB = -60.0
MAX_DB = 0.0

# Granice kolorów segmentów
YELLOW_DB = -18.0
RED_DB = -6.0

# Dynamika opadania (dB na sekundę)
DECAY_RATE_DB = 28.0
PEAK_HOLD_TIME_SEC = 0.9
PEAK_DECAY_RATE_DB = 24.0


def _generate_center_frequencies(count: int, f_min: float, f_max: float) -> list[float]:
    """Generuje środkowe częstotliwości pasm rozmieszczone logarytmicznie."""
    ratio = (f_max / f_min) ** (1.0 / (count - 1))
    return [f_min * (ratio ** i) for i in range(count)]


CENTER_FREQUENCIES = _generate_center_frequencies(NUM_BANDS, FREQ_MIN_HZ, FREQ_MAX_HZ)


def _format_freq_label(hz: float) -> str:
    """Formatuje częstotliwość do zwięzłej etykiety osi X (np. 20, 250, 1k, 8k)."""
    if hz >= 950:
        k = round(hz / 1000.0)
        return f"{k}k" if k >= 1 else f"{hz / 1000.0:.1f}k"
    return str(round(hz))


class SpectrumDataSimulator:
    """Symulator dynamicznej energii spektralnej muzyki w pasmach 20 Hz - 20 kHz."""

    def __init__(self, num_bands: int = NUM_BANDS):
        self.num_bands = num_bands
        self._phase = 0.0
        self._band_phases = [random.uniform(0, 6.28) for _ in range(num_bands)]
        self._band_speeds = [random.uniform(0.6, 2.4) for _ in range(num_bands)]

    def compute_levels(self, is_playing: bool, volume_percent: int) -> list[float]:
        """Oblicza aktualne poziomy energii w dBFS dla każdego pasma."""
        if not is_playing or volume_percent <= 0:
            return [MIN_DB] * self.num_bands

        vol_frac = max(0.01, min(1.0, volume_percent / 100.0))
        base_gain_db = 20.0 * math.log10(vol_frac)

        self._phase += 0.16

        # Rytm / uderzenia basowe (stopa 40-100 Hz, subbas 20-50 Hz)
        kick_pulse = (math.sin(self._phase * 2.5) ** 6) * 14.0
        snare_pulse = (math.sin(self._phase * 1.25 + 1.2) ** 8) * 11.0
        hihat_pulse = (math.sin(self._phase * 5.0) ** 4) * 8.0

        levels = []
        for i, freq in enumerate(CENTER_FREQUENCIES):
            self._band_phases[i] += 0.08 * self._band_speeds[i]
            mod = math.sin(self._band_phases[i]) * 4.5

            # Krzywa widmowa muzyki (spadek energii wysokich tonów, tzw. pink noise rolloff)
            # Pasma niskie (20-150 Hz): duża energia + kick
            if freq < 120:
                band_energy = -8.0 + kick_pulse * 0.9 + mod * 0.8
            # Niski środek i środek (150-1500 Hz): wokale, instrumenty
            elif freq < 1500:
                band_energy = -11.0 + snare_pulse * 0.8 + mod
            # Wyższy środek (1500-6000 Hz): obecność, werbel
            elif freq < 6000:
                band_energy = -14.0 + snare_pulse * 0.6 + hihat_pulse * 0.5 + mod
            # Góra (6000-20000 Hz): talerze, powietrze
            else:
                band_energy = -18.0 + hihat_pulse * 0.9 + mod * 0.7

            # Dodanie drobnych transjentów
            jitter = random.uniform(-1.8, 1.8)
            total_db = base_gain_db + band_energy + jitter
            total_db = max(MIN_DB, min(MAX_DB, total_db))
            levels.append(total_db)

        return levels


class AudioSpectrumAnalyzer(QWidget):
    """Widżet analizatora widma w czasie rzeczywistym z podziałką i wskaźnikami szczytów."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(140)
        self.setMinimumWidth(180)
        self.setToolTip("Analizator widma audio (20 Hz – 20 kHz)")

        self._levels = [MIN_DB] * NUM_BANDS
        self._peak_holds = [MIN_DB] * NUM_BANDS
        self._peak_times = [0.0] * NUM_BANDS

        self._last_tick = time.time()
        self._simulator = SpectrumDataSimulator(NUM_BANDS)

        # Timer animacji (~33 FPS)
        self._timer = QTimer(self)
        self._timer.setInterval(30)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

        # Stan sesji (aktualizowany przez okno aplikacji)
        self._is_playing = False
        self._volume = 100

    def update_session_state(self, is_playing: bool, volume: int):
        """Aktualizuje stan odtwarzania i głośność."""
        self._is_playing = is_playing
        self._volume = volume

    def reset(self):
        """Płynnie zeruje widmo do ciszy."""
        self._levels = [MIN_DB] * NUM_BANDS
        self._peak_holds = [MIN_DB] * NUM_BANDS
        self._peak_times = [0.0] * NUM_BANDS
        self.update()

    def _on_tick(self):
        now = time.time()
        dt = now - self._last_tick
        self._last_tick = now

        # Pobieranie nowych poziomów docelowych
        target_levels = self._simulator.compute_levels(self._is_playing, self._volume)

        # Aktualizacja poziomów i peak hold (atak natychmiastowy, płynny decay)
        for i in range(NUM_BANDS):
            target = target_levels[i]

            # Atak
            if target >= self._levels[i]:
                self._levels[i] = target
            else:
                # Opadanie
                self._levels[i] = max(MIN_DB, self._levels[i] - DECAY_RATE_DB * dt)

            # Peak hold
            if target >= self._peak_holds[i]:
                self._peak_holds[i] = target
                self._peak_times[i] = now
            elif now - self._peak_times[i] > PEAK_HOLD_TIME_SEC:
                self._peak_holds[i] = max(self._levels[i], self._peak_holds[i] - PEAK_DECAY_RATE_DB * dt)

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        w = self.width()
        h = self.height()

        # Tło
        painter.fillRect(0, 0, w, h, QColor("#141414"))
        painter.setPen(QColor("#2c2c2c"))
        painter.drawRect(0, 0, w - 1, h - 1)

        # Geometria wykresu
        pad_left = 6
        pad_right = 6
        pad_top = 8
        axis_h = 16
        plot_h = h - pad_top - axis_h
        plot_w = w - pad_left - pad_right

        if plot_w <= 0 or plot_h <= 0:
            return

        # Poziome linie siatki dBFS
        grid_ticks = [
            (0.0, " 0"),
            (-6.0, "-6"),
            (-18.0, "-18"),
            (-36.0, "-36"),
        ]

        grid_font = QFont("Consolas", 6)
        painter.setFont(grid_font)

        for db_val, label in grid_ticks:
            frac = (db_val - MIN_DB) / (MAX_DB - MIN_DB)
            y = int(pad_top + (1.0 - frac) * plot_h)

            if db_val >= RED_DB:
                line_col = QColor("#3a1818")
            elif db_val >= YELLOW_DB:
                line_col = QColor("#332b12")
            else:
                line_col = QColor("#1e2820")

            painter.setPen(line_col)
            painter.drawLine(pad_left, y, pad_left + plot_w, y)

        # Rozmieszczenie słupków
        total_bars = NUM_BANDS
        spacing = 2
        available_w = plot_w - (total_bars - 1) * spacing
        bar_w = max(2, int(available_w / total_bars))

        # Obliczenie rzeczywistego marginesu wyśrodkowania słupków
        used_w = total_bars * bar_w + (total_bars - 1) * spacing
        start_x = pad_left + max(0, (plot_w - used_w) // 2)

        # Segmenty pionowe LED
        step = 3
        num_segments = plot_h // step

        for b_idx in range(total_bars):
            bx = start_x + b_idx * (bar_w + spacing)
            level_db = self._levels[b_idx]
            peak_db = self._peak_holds[b_idx]

            # Rysowanie segmentów słupka
            for seg in range(num_segments):
                y_seg = pad_top + plot_h - (seg + 1) * step
                frac = (seg + 0.5) / num_segments
                seg_db = MIN_DB + frac * (MAX_DB - MIN_DB)

                # Kolorystyka LED
                if seg_db >= RED_DB:
                    lit_color = QColor("#ff3333")
                    dim_color = QColor("#281010")
                elif seg_db >= YELLOW_DB:
                    lit_color = QColor("#f1c40f")
                    dim_color = QColor("#282208")
                else:
                    lit_color = QColor("#2ecc71")
                    dim_color = QColor("#0d2416")

                color = lit_color if seg_db <= level_db else dim_color
                painter.fillRect(bx, y_seg, bar_w, step - 1, color)

            # Znacznik Peak Hold (kreska szczytu)
            if peak_db > MIN_DB:
                p_frac = (peak_db - MIN_DB) / (MAX_DB - MIN_DB)
                py = int(pad_top + (1.0 - p_frac) * plot_h)
                py = max(pad_top, min(pad_top + plot_h - 2, py))

                if peak_db >= RED_DB:
                    peak_color = QColor("#ffffff")
                elif peak_db >= YELLOW_DB:
                    peak_color = QColor("#fff3aa")
                else:
                    peak_color = QColor("#d0ffd0")

                pen = QPen(peak_color)
                pen.setWidth(2)
                painter.setPen(pen)
                painter.drawLine(bx, py, bx + bar_w - 1, py)

        # Oznaczenia częstotliwości pod osią X
        axis_font = QFont("Arial", 6)
        painter.setFont(axis_font)
        painter.setPen(QColor("#777777"))

        # Wybrane indeksy pasm do wyświetlenia etykiet (aby się nie nakładały)
        labeled_indices = [0, 3, 6, 9, 12, 15, 18, 21, 23]
        for idx in labeled_indices:
            if idx < total_bars:
                bx = start_x + idx * (bar_w + spacing)
                lbl = _format_freq_label(CENTER_FREQUENCIES[idx])
                # Wyśrodkowanie tekstu pod słupkiem
                painter.drawText(bx - 6, h - 3, lbl)
