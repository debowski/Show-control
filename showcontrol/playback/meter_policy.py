"""Polityka stanu miernika szczytowego: pomiar, cisza, brak pomiaru.

Moduł czysty: bez Qt, bez VLC, bez WASAPI. Miernik w UI dostaje wyłącznie
wynik tej funkcji, więc każdą regułę da się przetestować bez sprzętu.
Decyzja: ``docs/adr/0006-miernik-realny-sygnal.md``; pojęcia: ``GLOSSARY.md``
§ Pomiar sygnału.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

MIN_DB = -60.0
MAX_DB = 0.0
MIN_DBFS = MIN_DB
MAX_DBFS = MAX_DB

FULL_SCALE = 32768.0

#: Po tylu sekundach bez świeżych danych miernik nie wie, co gra.
STALE_AFTER_SEC = 0.25


class MeterState(Enum):
    """Trzy stany miernika. Brak pomiaru nie jest ciszą."""

    MEASURED = "measured"
    SILENT = "silent"
    NO_MEASUREMENT = "no_measurement"


@dataclass(frozen=True)
class LevelSample:
    """Pomiar z jednego bloku audio."""

    left_db: float
    right_db: float
    measured_at: float  # time.monotonic()


def peak_to_db(peak: int) -> float:
    """Szczytowa amplituda int16 -> dBFS, obcięta do zakresu miernika."""
    if peak <= 0:
        return MIN_DB
    amplitude = min(abs(peak), int(FULL_SCALE)) / FULL_SCALE
    if amplitude <= 0.0:
        return MIN_DB
    return max(MIN_DB, min(MAX_DB, 20.0 * math.log10(amplitude)))


def block_peaks(data: memoryview, channels: int) -> tuple[float, float]:
    """Szczyty L i R z jednego bloku int16 (interleaved).

    Kanał 0 trafia na L, kanał 1 na R; mono trafia na oba. Kanały dalsze
    (surround) są ignorowane — miernik jest stereo, jak konsola.
    """
    if channels <= 0 or len(data) < channels:
        return (MIN_DB, MIN_DB)

    peaks = []
    for channel in range(channels):
        values = data[channel::channels]
        if len(values) == 0:
            peaks.append(0)
        else:
            peaks.append(max(max(values), -min(values)))

    left = peak_to_db(peaks[0])
    right = peak_to_db(peaks[1] if len(peaks) > 1 else peaks[0])
    return (left, right)


def resolve_state(
    *,
    is_playing: bool,
    sample: LevelSample | None,
    now: float,
    stale_after: float = STALE_AFTER_SEC,
) -> MeterState:
    """Rozstrzyga, co miernik ma pokazać.

    - sesja nie gra -> cisza (wiemy, że nie gra; nie trzeba mierzyć),
    - gra i ma świeży pomiar nad podłogą -> pomiar,
    - gra i zmierzona cisza -> cisza,
    - gra, a danych nie ma albo są stare -> brak pomiaru.
    """
    if not is_playing:
        return MeterState.SILENT
    if sample is None:
        return MeterState.NO_MEASUREMENT
    if now - sample.measured_at > stale_after:
        return MeterState.NO_MEASUREMENT
    if max(sample.left_db, sample.right_db) <= MIN_DB:
        return MeterState.SILENT
    return MeterState.MEASURED
