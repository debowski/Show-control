"""Wiring pomiaru: callback PortAudio zapisuje szczyt bloku. Bez WASAPI i Qt."""

import array
import time
from types import SimpleNamespace

from showcontrol.playback.audio_meter import AudioMeter
from showcontrol.playback.meter_policy import MIN_DB


def _stereo_block(*frames):
    """Buduje blok int16 interleaved z par (L, R)."""
    data = array.array("h")
    for left, right in frames:
        data.append(left)
        data.append(right)
    return data.tobytes()


class _FakePortAudio(SimpleNamespace):
    """Minimalne API pyaudiowpatch, którego używa callback."""

    paContinue = 0


def test_callback_stores_peak_levels():
    meter = AudioMeter()
    callback = meter._make_callback(_FakePortAudio, 2)

    before = time.monotonic()
    out_data, flag = callback(_stereo_block((16384, 0), (-16384, 0)), 2, None, 0)

    assert out_data is None
    assert flag == _FakePortAudio.paContinue
    sample = meter.latest()
    assert sample is not None
    assert round(sample.left_db, 2) == -6.02
    assert sample.right_db == MIN_DB
    assert before <= sample.measured_at <= time.monotonic()


def test_empty_block_keeps_previous_sample():
    meter = AudioMeter()
    callback = meter._make_callback(_FakePortAudio, 2)
    callback(_stereo_block((16384, 16384)), 1, None, 0)
    first = meter.latest()

    callback(b"", 0, None, 0)

    assert meter.latest() is first


class _FakeDevice:
    def __init__(self, index):
        self.index = index

    def get_default_wasapi_loopback(self):
        return {"index": self.index}


class _FakeStream:
    def __init__(self, active=True):
        self._active = active

    def is_active(self):
        return self._active


def test_healthy_stream_still_points_at_default_device():
    meter = AudioMeter()
    meter._device_index = 1

    assert meter._healthy(_FakeDevice(1), _FakeStream()) is True


def test_device_change_forces_reopen():
    meter = AudioMeter()
    meter._device_index = 1

    assert meter._healthy(_FakeDevice(2), _FakeStream()) is False


def test_stopped_stream_forces_reopen():
    meter = AudioMeter()
    meter._device_index = 1

    assert meter._healthy(_FakeDevice(1), _FakeStream(active=False)) is False


def test_device_error_forces_reopen():
    meter = AudioMeter()
    meter._device_index = 1

    class _BrokenDevice:
        def get_default_wasapi_loopback(self):
            raise OSError("PortAudio error")

    assert meter._healthy(_BrokenDevice(), _FakeStream()) is False
