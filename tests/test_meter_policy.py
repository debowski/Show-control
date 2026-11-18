"""Stany miernika szczytowego według ADR 0006. Bez Qt, VLC i WASAPI."""

import array

from showcontrol.playback.meter_policy import (
    MIN_DB,
    LevelSample,
    MeterState,
    block_peaks,
    peak_to_db,
    resolve_state,
)


def _block(*frames):
    """Buduje blok int16 interleaved z par (L, R)."""
    data = array.array("h")
    for left, right in frames:
        data.append(left)
        data.append(right)
    return memoryview(data)


def _sample(left_db, right_db, measured_at=100.0):
    return LevelSample(left_db=left_db, right_db=right_db, measured_at=measured_at)


# --- peak_to_db ---------------------------------------------------------


def test_full_scale_is_zero_db():
    assert peak_to_db(32767) <= 0.0
    assert peak_to_db(32767) > -1.0


def test_half_scale_is_minus_six_db():
    assert round(peak_to_db(16384), 2) == -6.02


def test_zero_and_silence_floor_at_min_db():
    assert peak_to_db(0) == MIN_DB
    assert peak_to_db(-5) == MIN_DB


def test_values_below_floor_are_clamped():
    assert peak_to_db(1) == MIN_DB


def test_over_full_scale_is_clamped_to_zero():
    assert peak_to_db(40000) == 0.0


# --- block_peaks --------------------------------------------------------


def test_stereo_peaks_are_separate():
    left_db, right_db = block_peaks(_block((-16384, 100), (16384, 200)), 2)
    assert round(left_db, 2) == -6.02
    assert round(right_db, 1) == round(peak_to_db(200), 1)


def test_negative_half_wave_counts_as_peak():
    left_db, _ = block_peaks(_block((0, 0), (-16384, 0)), 2)
    assert round(left_db, 2) == -6.02


def test_mono_feeds_both_channels():
    left_db, right_db = block_peaks(memoryview(array.array("h", [16384, -16384])), 1)
    assert left_db == right_db


def test_surround_uses_front_channels_only():
    data = memoryview(array.array("h", [16384, 0, 30000, 30000]))
    left_db, right_db = block_peaks(data, 4)
    assert round(left_db, 2) == -6.02
    assert right_db == MIN_DB


def test_empty_block_is_silence():
    assert block_peaks(memoryview(array.array("h")), 2) == (MIN_DB, MIN_DB)


# --- resolve_state ------------------------------------------------------


def test_not_playing_is_silence_even_with_fresh_data():
    state = resolve_state(is_playing=False, sample=_sample(-3.0, -3.0, 100.0), now=100.1)
    assert state is MeterState.SILENT


def test_playing_with_fresh_sample_is_measured():
    state = resolve_state(is_playing=True, sample=_sample(-6.0, -7.0, 100.0), now=100.1)
    assert state is MeterState.MEASURED


def test_playing_without_sample_is_no_measurement():
    state = resolve_state(is_playing=True, sample=None, now=100.0)
    assert state is MeterState.NO_MEASUREMENT


def test_playing_with_stale_sample_is_no_measurement():
    state = resolve_state(is_playing=True, sample=_sample(-6.0, -6.0, 100.0), now=101.0)
    assert state is MeterState.NO_MEASUREMENT


def test_stale_threshold_is_inclusive_boundary():
    fresh = resolve_state(is_playing=True, sample=_sample(-6.0, -6.0, 100.0), now=100.25)
    stale = resolve_state(is_playing=True, sample=_sample(-6.0, -6.0, 100.0), now=100.26)
    assert fresh is MeterState.MEASURED
    assert stale is MeterState.NO_MEASUREMENT


def test_measured_floor_is_silence_not_no_measurement():
    state = resolve_state(is_playing=True, sample=_sample(MIN_DB, MIN_DB, 100.0), now=100.1)
    assert state is MeterState.SILENT
