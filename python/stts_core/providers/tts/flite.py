"""Flite TTS Provider for STTS."""

from __future__ import annotations

import shutil
import subprocess

from stts_core.providers import TTSProvider


class FliteTTS(TTSProvider):
    """Flite TTS - lightweight, fast speech synthesis."""

    name = "flite"

    @classmethod
    def is_available(cls, info):
        if shutil.which("flite"):
            return True, "flite found"
        return False, "install flite"

    def speak(self, text: str) -> None:
        cmd = shutil.which("flite")
        if not cmd:
            return
        try:
            args = [cmd]
            if self.voice:
                args += ["-voice", str(self.voice)]
            args += ["-t", text]
            subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            return
