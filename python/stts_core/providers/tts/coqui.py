"""Coqui TTS Provider for STTS."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from stts_core.providers import TTSProvider
from ...shell_utils import cprint, Colors, play_audio


class CoquiTTS(TTSProvider):
    """Coqui TTS - open-source neural TTS."""

    name = "coqui-tts"

    @classmethod
    def is_available(cls, info):
        if shutil.which("tts"):
            return True, "tts found"
        try:
            import TTS
            return True, "coqui-tts installed"
        except ImportError:
            return False, "pip install coqui-tts"

    def speak(self, text: str) -> None:
        no_play = os.environ.get("STTS_TTS_NO_PLAY", "").strip().lower() in ("1", "true", "yes", "y")

        try:
            with tempfile.NamedTemporaryFile(prefix="stts_coqui_", suffix=".wav", delete=False) as f:
                out_path = f.name

            # Try command line first
            if shutil.which("tts"):
                cmd = ["tts", "--text", text, "--out_path", out_path]
                if self.voice:
                    cmd.extend(["--model_name", self.voice])
                res = subprocess.run(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=60,
                )
                if res.returncode == 0 and Path(out_path).exists() and not no_play:
                    play_audio(out_path)
            else:
                # Try Python API
                from TTS.api import TTS as CoquiTTSApi
                tts = CoquiTTSApi(model_name=self.voice or "tts_models/en/ljspeech/tacotron2-DDC")
                tts.tts_to_file(text=text, file_path=out_path)
                if not no_play:
                    play_audio(out_path)

            try:
                Path(out_path).unlink(missing_ok=True)
            except Exception:
                pass
        except Exception as e:
            cprint(Colors.YELLOW, f"⚠️ Coqui TTS error: {e}")
