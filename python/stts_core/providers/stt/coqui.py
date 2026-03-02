"""Coqui STT Provider for STTS."""

from __future__ import annotations

import os
import subprocess
import sys
import wave
from pathlib import Path
from typing import Optional

from stts_core.providers import STTProvider
from stts_core.config import MODELS_DIR
from stts_core.shell_utils import cprint, Colors
from stts_core.text import TextNormalizer


class CoquiSTT(STTProvider):
    """Coqui STT - lightweight, CPU-friendly, good for Polish accents."""

    name = "coqui"
    description = "Offline, lightweight STT (Coqui/DeepSpeech)"
    min_ram_gb = 0.5

    @classmethod
    def is_available(cls, info):
        try:
            from stt import Model
            return True, "coqui-stt installed"
        except ImportError:
            return False, "pip install coqui-stt"

    @classmethod
    def get_recommended_model(cls, info) -> Optional[str]:
        return "model.tflite"

    def transcribe(self, audio_path: str) -> str:
        try:
            from stt import Model
        except ImportError:
            cprint(Colors.RED, "❌ coqui-stt not installed: pip install coqui-stt")
            return ""

        model_path = self.model or str(MODELS_DIR / "coqui" / "model.tflite")
        if not Path(model_path).exists():
            cprint(Colors.RED, f"❌ Coqui model not found: {model_path}")
            return ""

        try:
            wf = wave.open(audio_path, "rb")
            audio = wf.readframes(wf.getnframes())
            wf.close()

            model = Model(model_path)
            text = model.stt(audio)
            return TextNormalizer.normalize(text or "", self.language)
        except Exception as e:
            cprint(Colors.RED, f"❌ Coqui STT error: {e}")
            return ""
