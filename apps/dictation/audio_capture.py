"""Push-to-talk microphone capture."""

from __future__ import annotations

import tempfile
import threading
import wave
from pathlib import Path

import numpy as np


class PushToTalkRecorder:
    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self._frames: list[np.ndarray] = []
        self._stream = None
        self._lock = threading.Lock()
        self._recording = False

    @property
    def recording(self) -> bool:
        return self._recording

    def start(self) -> None:
        import sounddevice as sd

        with self._lock:
            if self._recording:
                return
            self._frames = []
            self._recording = True

            def _callback(indata, frames, time_info, status):  # noqa: ARG001
                if status:
                    pass
                with self._lock:
                    if self._recording:
                        self._frames.append(indata.copy())

            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
                callback=_callback,
            )
            self._stream.start()

    def stop(self) -> Path | None:
        with self._lock:
            if not self._recording:
                return None
            self._recording = False
            stream = self._stream
            self._stream = None
            frames = list(self._frames)
            self._frames = []

        if stream is not None:
            stream.stop()
            stream.close()

        if not frames:
            return None
        audio = np.concatenate(frames, axis=0)
        if audio.ndim > 1:
            audio = audio[:, 0]
        # float32 [-1,1] → int16 PCM
        pcm = np.clip(audio, -1.0, 1.0)
        pcm = (pcm * 32767.0).astype(np.int16)

        tmp = Path(tempfile.mkstemp(prefix="dictate-", suffix=".wav")[1])
        with wave.open(str(tmp), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(pcm.tobytes())
        return tmp
