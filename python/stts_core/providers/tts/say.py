"""Say (macOS) TTS Provider for STTS."""

from __future__ import annotations

import shutil
import subprocess

from stts_core.providers import TTSProvider


class SayTTS(TTSProvider):
    """macOS say command - built-in TTS."""

    name = "say"

    @classmethod
    def is_available(cls, info):
        if info.os_name == "darwin" and shutil.which("say"):
            return True, "say found"
        return False, "macOS only (say)"

    def speak(self, text: str) -> None:
        cmd = shutil.which("say")
        if not cmd:
            return
        try:
            args = [cmd]
            if self.voice:
                args += ["-v", str(self.voice)]
            args.append(text)
            subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            return
