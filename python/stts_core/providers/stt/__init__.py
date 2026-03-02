from __future__ import annotations

from .whisper_cpp import WhisperCppSTT
from .deepgram import DeepgramSTT
from .vosk import VoskSTT
from .faster_whisper import FasterWhisperSTT
from .coqui import CoquiSTT
from .picovoice import PicovoiceSTT

__all__ = [
    "WhisperCppSTT",
    "DeepgramSTT",
    "VoskSTT",
    "FasterWhisperSTT",
    "CoquiSTT",
    "PicovoiceSTT",
]
