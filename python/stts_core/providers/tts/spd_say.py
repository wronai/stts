"""Spd-say TTS Provider for STTS."""

from __future__ import annotations

import shutil
import subprocess

from stts_core.providers import TTSProvider


class SpdSayTTS(TTSProvider):
    """Speech Dispatcher TTS - system integration."""

    name = "spd-say"

    @classmethod
    def is_available(cls, info):
        if shutil.which("spd-say"):
            return True, "spd-say found"
        return False, "install speech-dispatcher (spd-say)"

    def speak(self, text: str) -> None:
        cmd = shutil.which("spd-say")
        if not cmd:
            return
        try:
            subprocess.run([cmd, "-l", str(self.voice), text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            return
