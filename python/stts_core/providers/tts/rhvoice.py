"""RHVoice TTS Provider for STTS."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from stts_core.providers import TTSProvider
from stts_core.shell_utils import cprint, Colors, play_audio


class RHVoiceTTS(TTSProvider):
    """RHVoice - native Polish TTS, fast CPU."""

    name = "rhvoice"

    @classmethod
    def is_available(cls, info):
        if shutil.which("RHVoice-test") or shutil.which("rhvoice-test"):
            return True, "rhvoice found"
        return False, "apt install rhvoice rhvoice-polish"

    def speak(self, text: str) -> None:
        cmd = shutil.which("RHVoice-test") or shutil.which("rhvoice-test")
        if not cmd:
            cprint(Colors.YELLOW, "⚠️ RHVoice not found")
            return

        no_play = os.environ.get("STTS_TTS_NO_PLAY", "").strip().lower() in ("1", "true", "yes", "y")

        try:
            voice = self.voice or "Anna"  # Polish voice

            with tempfile.NamedTemporaryFile(prefix="stts_rhvoice_", suffix=".wav", delete=False) as f:
                out_path = f.name

            proc = subprocess.run(
                [cmd, "-p", voice, "-o", out_path],
                input=text,
                text=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            if not no_play and Path(out_path).exists():
                play_audio(out_path)

            try:
                Path(out_path).unlink(missing_ok=True)
            except Exception:
                pass
        except Exception as e:
            cprint(Colors.YELLOW, f"⚠️ RHVoice error: {e}")
