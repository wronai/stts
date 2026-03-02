"""Faster-Whisper STT Provider for STTS."""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Optional

from stts_core.providers import STTProvider
from stts_core.shell_utils import cprint, Colors
from stts_core.text import TextNormalizer


class FasterWhisperSTT(STTProvider):
    """faster-whisper STT provider - CTranslate2-optimized Whisper."""

    name = "faster_whisper"
    description = "Offline, fast CTranslate2 Whisper (GPU/CPU)"
    min_ram_gb = 1.0
    models = [
        ("tiny", "tiny", 0.08),
        ("base", "base", 0.15),
        ("small", "small", 0.5),
        ("medium", "medium", 1.5),
        ("large-v3", "large-v3", 3.0),
        ("distil-large-v3", "distil-large-v3", 1.5),
    ]

    @classmethod
    def is_available(cls, info):
        try:
            from faster_whisper import WhisperModel
            return True, "faster-whisper installed"
        except ImportError:
            return False, "pip install faster-whisper"

    @classmethod
    def install(cls, info) -> bool:
        try:
            res = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-U", "faster-whisper"],
                capture_output=True,
                text=True,
                timeout=300,
            )
            return res.returncode == 0
        except Exception:
            return False

    @classmethod
    def get_recommended_model(cls, info) -> str:
        if info.ram_gb < 2:
            return "tiny"
        if info.ram_gb < 4:
            return "base"
        if info.ram_gb < 8:
            return "small"
        if info.ram_gb < 16:
            return "medium"
        return "large-v3"

    def transcribe(self, audio_path: str) -> str:
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            cprint(Colors.RED, "❌ faster-whisper not installed: pip install faster-whisper")
            return ""

        model_name = self.model or "base"

        # Determine compute type
        compute_type = (
            (self.config.get("faster_whisper_compute_type") if isinstance(self.config, dict) else None)
            or os.environ.get("STTS_FASTER_WHISPER_COMPUTE_TYPE", "")
        )
        compute_type = str(compute_type).strip() or "int8"

        # Determine device
        device = (
            (self.config.get("faster_whisper_device") if isinstance(self.config, dict) else None)
            or os.environ.get("STTS_FASTER_WHISPER_DEVICE", "")
        )
        device = str(device).strip() or "auto"

        try:
            model = WhisperModel(model_name, device=device, compute_type=compute_type)

            lang = str(self.language or "").strip()
            if lang.lower() in ("", "auto"):
                segments, info = model.transcribe(audio_path)
            else:
                segments, info = model.transcribe(audio_path, language=lang)

            text = " ".join(seg.text for seg in segments).strip()
            return TextNormalizer.normalize(text, self.language)

        except Exception as e:
            cprint(Colors.RED, f"❌ faster-whisper error: {e}")
            return ""
