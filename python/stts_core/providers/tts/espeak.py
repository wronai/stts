"""Espeak TTS Provider for STTS."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from stts_core.providers import TTSProvider
from stts_core.shell_utils import cprint, Colors


class EspeakTTS(TTSProvider):
    """Espeak TTS - lightweight, multi-language speech synthesis."""

    name = "espeak"

    @classmethod
    def is_available(cls, info):
        if shutil.which("espeak") or shutil.which("espeak-ng"):
            return True, "espeak found"
        return False, "apt install espeak / espeak-ng"

    def speak(self, text: str) -> None:
        cmd = shutil.which("espeak-ng") or shutil.which("espeak")
        if not cmd:
            cprint(Colors.YELLOW, "⚠️  Brak espeak/espeak-ng")
            return
        try:
            no_play = os.environ.get("STTS_TTS_NO_PLAY", "").strip().lower() in ("1", "true", "yes", "y")
            if no_play:
                with tempfile.NamedTemporaryFile(prefix="stts_espeak_", suffix=".wav", delete=False) as f:
                    out_path = f.name
                res = subprocess.run(
                    [cmd, "-v", self.voice, "-s", "160", "-w", out_path, text],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                try:
                    Path(out_path).unlink(missing_ok=True)
                except Exception:
                    pass
            else:
                res = subprocess.run(
                    [cmd, "-v", self.voice, "-s", "160", text],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            if getattr(res, "returncode", 0) != 0:
                cprint(Colors.YELLOW, f"⚠️  espeak returncode={res.returncode}")
        except Exception:
            return
