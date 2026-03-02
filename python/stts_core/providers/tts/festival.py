"""Festival TTS Provider for STTS."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from stts_core.providers import TTSProvider
from stts_core.shell_utils import cprint, Colors, play_audio


class FestivalTTS(TTSProvider):
    """Festival TTS - classic, ultra-lightweight."""

    name = "festival"

    @classmethod
    def is_available(cls, info):
        if shutil.which("text2wave") and shutil.which("aplay"):
            return True, "festival found"
        if shutil.which("festival"):
            return True, "festival found"
        return False, "apt install festival festvox-kallpc16k"

    def speak(self, text: str) -> None:
        no_play = os.environ.get("STTS_TTS_NO_PLAY", "").strip().lower() in ("1", "true", "yes", "y")

        try:
            with tempfile.NamedTemporaryFile(prefix="stts_festival_", suffix=".wav", delete=False) as f:
                out_path = f.name

            # Use text2wave if available
            if shutil.which("text2wave"):
                proc = subprocess.run(
                    ["text2wave", "-o", out_path],
                    input=text,
                    text=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                # Fallback to festival --tts
                proc = subprocess.run(
                    ["festival", "--tts"],
                    input=text,
                    text=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return  # festival --tts plays directly

            if not no_play and Path(out_path).exists():
                play_audio(out_path)

            try:
                Path(out_path).unlink(missing_ok=True)
            except Exception:
                pass
        except Exception as e:
            cprint(Colors.YELLOW, f"⚠️ Festival TTS error: {e}")
