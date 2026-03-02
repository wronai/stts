from __future__ import annotations

from .espeak import EspeakTTS
from .piper import PiperTTS
from .spd_say import SpdSayTTS
from .say import SayTTS
from .flite import FliteTTS
from .festival import FestivalTTS
from .rhvoice import RHVoiceTTS
from .kokoro import KokoroTTS
from .coqui import CoquiTTS

__all__ = [
    "EspeakTTS",
    "PiperTTS",
    "SpdSayTTS",
    "SayTTS",
    "FliteTTS",
    "FestivalTTS",
    "RHVoiceTTS",
    "KokoroTTS",
    "CoquiTTS",
]
