"""Pomiar poziomu sygnału wyjściowego przez WASAPI loopback.

Czyta domyślne urządzenie renderujące w trybie współdzielonym, więc mierzy
to, co naprawdę wychodzi z aplikacji: po głośności, po fade i po głośności
końcówki. Decyzja i odrzucone drogi: ``docs/adr/0006-miernik-realny-sygnal.md``.

Callback PortAudio działa we własnym wątku, więc **nie dotyka Qt** — tylko
zapisuje próbkę pod zamkiem. UI czyta ją przez :meth:`AudioMeter.latest`.

Blokujący ``stream.read()`` nie wchodzi w grę: gdy nic nie jest renderowane,
WASAPI nie dostarcza danych i odczyt zawiesza się na stałe.
"""

from __future__ import annotations

import logging
import threading
import time

from showcontrol.playback.meter_policy import LevelSample, block_peaks

logger = logging.getLogger(__name__)

#: Rozmiar bloku w próbkach na kanał (~21 ms przy 48 kHz).
BLOCK_FRAMES = 1024

#: Co ile sprawdzamy, czy domyślne urządzenie się nie zmieniło i czy strumień żyje.
DEVICE_CHECK_SEC = 1.0

#: Odstęp między próbami otwarcia urządzenia.
RETRY_SEC = 2.0


class AudioMeter:
    """Właściciel strumienia loopback i ostatniego pomiaru.

    Klasa nie zna sesji odtwarzania — decyzję „pomiar / cisza / brak pomiaru"
    podejmuje :func:`showcontrol.playback.meter_policy.resolve_state`.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._sample: LevelSample | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._device_index: int | None = None

    # --- API dla UI -----------------------------------------------------

    def start(self) -> None:
        """Uruchamia wątek nadzorujący. Bezpieczne wielokrotnie."""
        if self._thread is not None:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._supervise, name="audio-meter", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Zatrzymuje pomiar i zamyka strumień."""
        self._stop.set()
        thread = self._thread
        self._thread = None
        if thread is not None:
            thread.join(timeout=3.0)

    def latest(self) -> LevelSample | None:
        """Ostatni pomiar albo ``None``, jeśli jeszcze żadnego nie było."""
        with self._lock:
            return self._sample

    # --- wątek nadzorujący ----------------------------------------------

    def _supervise(self) -> None:
        try:
            import pyaudiowpatch as pyaudio
        except Exception:  # pragma: no cover - zależy od środowiska
            logger.warning("pyaudiowpatch niedostępny — miernik bez pomiaru")
            return

        pa = None
        stream = None
        try:
            while not self._stop.is_set():
                if pa is None:
                    try:
                        pa = pyaudio.PyAudio()
                    except Exception:
                        logger.exception("Nie udało się zainicjalizować PortAudio")
                        self._stop.wait(RETRY_SEC)
                        continue

                if stream is None:
                    stream = self._open(pa, pyaudio)
                    if stream is None:
                        self._stop.wait(RETRY_SEC)
                        continue
                elif not self._healthy(pa, stream):
                    stream = self._close(stream)

                self._stop.wait(DEVICE_CHECK_SEC)
        finally:
            self._close(stream)
            if pa is not None:
                try:
                    pa.terminate()
                except Exception:
                    logger.debug("PortAudio terminate nie powiódł się", exc_info=True)

    def _open(self, pa, pyaudio):
        """Otwiera loopback domyślnego urządzenia. ``None`` = nie udało się."""
        try:
            info = pa.get_default_wasapi_loopback()
        except Exception:
            logger.warning("Brak domyślnego urządzenia WASAPI do pomiaru")
            return None

        index = info["index"]
        rate = int(info.get("defaultSampleRate") or 48000)
        channels = int(info.get("maxInputChannels") or 2)

        try:
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=rate,
                frames_per_buffer=BLOCK_FRAMES,
                input=True,
                input_device_index=index,
                stream_callback=self._make_callback(pyaudio, channels),
            )
            stream.start_stream()
        except Exception:
            logger.exception("Nie udało się otworzyć loopbacku urządzenia %r", info.get("name"))
            return None

        self._device_index = index
        logger.info("Miernik: loopback %r, %d Hz, %d kanałów", info.get("name"), rate, channels)
        return stream

    def _healthy(self, pa, stream) -> bool:
        """Czy strumień żyje i nadal wskazuje domyślne urządzenie."""
        try:
            if not stream.is_active():
                logger.warning("Strumień pomiaru zatrzymany — ponawiam otwarcie")
                return False
            if pa.get_default_wasapi_loopback()["index"] != self._device_index:
                logger.info("Zmiana domyślnego urządzenia — przełączam pomiar")
                return False
        except Exception:
            logger.warning("Nie można sprawdzić urządzenia pomiaru", exc_info=True)
            return False
        return True

    def _close(self, stream):
        if stream is not None:
            try:
                stream.stop_stream()
            except Exception:
                logger.debug("stop_stream nie powiódł się", exc_info=True)
            try:
                stream.close()
            except Exception:
                logger.debug("close strumienia nie powiódł się", exc_info=True)
        self._device_index = None
        return None

    def _make_callback(self, pyaudio, channels: int):
        """Callback PortAudio: mierzy blok i zapisuje wynik pod zamkiem."""

        def callback(in_data, frame_count, time_info, status):
            if in_data:
                left_db, right_db = block_peaks(memoryview(in_data).cast("h"), channels)
                sample = LevelSample(left_db=left_db, right_db=right_db, measured_at=time.monotonic())
                with self._lock:
                    self._sample = sample
            return (None, pyaudio.paContinue)

        return callback
