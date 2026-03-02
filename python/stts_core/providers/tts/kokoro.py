"""Kokoro TTS Provider for STTS."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from stts_core.providers import TTSProvider
from stts_core.shell_utils import cprint, Colors, play_audio


class KokoroTTS(TTSProvider):
    """Kokoro-82M - new open-source, fast on CPU."""

    name = "kokoro"

    @classmethod
    def is_available(cls, info):
        try:
            import kokoro
            return True, "kokoro installed"
        except ImportError:
            return False, "pip install kokoro"

    def speak(self, text: str) -> None:
        try:
            import kokoro
        except ImportError:
            cprint(Colors.YELLOW, "⚠️ kokoro not installed: pip install kokoro")
            return

        no_play = os.environ.get("STTS_TTS_NO_PLAY", "").strip().lower() in ("1", "true", "yes", "y")

        try:
            with tempfile.NamedTemporaryFile(prefix="stts_kokoro_", suffix=".wav", delete=False) as f:
                out_path = f.name

            # Kokoro API (simplified)
            model = kokoro.KokoroTTS()
            audio = model.generate(text)
            import scipy.io.wavfile as wav
            wav.write(out_path, 24000, audio)

            if not no_play:
                play_audio(out_path)

            try:
                Path(out_path).unlink(missing_ok=True)
            except Exception:
                pass
        except Exception as e:
            cprint(Colors.YELLOW, f"⚠️ Kokoro TTS error: {e}")
