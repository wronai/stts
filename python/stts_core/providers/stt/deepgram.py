"""Deepgram STT Provider for STTS."""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path
from typing import Optional

from stts_core.providers import STTProvider
from stts_core.shell_utils import cprint, Colors
from stts_core.text import TextNormalizer


class DeepgramSTT(STTProvider):
    """Online STT (Deepgram REST)."""

    name = "deepgram"
    description = "Online STT (Deepgram REST)"
    min_ram_gb = 0.1

    @classmethod
    def is_available(cls, info):
        key = os.environ.get("STTS_DEEPGRAM_KEY", "").strip()
        if not key:
            return False, "set STTS_DEEPGRAM_KEY"
        return True, "Deepgram key set"

    @classmethod
    def get_recommended_model(cls, info) -> Optional[str]:
        return "nova-2"

    def transcribe(self, audio_path: str) -> str:
        key = os.environ.get("STTS_DEEPGRAM_KEY", "").strip()
        if not key:
            return ""

        model = (
            (self.config.get("stt_model") if isinstance(self.config, dict) else None)
            or os.environ.get("STTS_DEEPGRAM_MODEL", "")
            or "nova-2"
        )
        model = str(model).strip() or "nova-2"

        language = (
            (self.language or "pl")
            if str(self.language or "").strip()
            else (os.environ.get("STTS_LANGUAGE", "pl") or "pl")
        )
        language = str(language).strip() or "pl"

        try:
            data = Path(audio_path).read_bytes()
        except Exception:
            return ""

        params = {
            "model": model,
            "language": language,
            "smart_format": "true",
        }
        url = "https://api.deepgram.com/v1/listen?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={
                "Authorization": f"Token {key}",
                "Content-Type": "audio/wav",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                payload = resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            cprint(Colors.RED, f"❌ Deepgram error: {e}")
            return ""

        try:
            j = json.loads(payload)
            txt = (
                (((j.get("results") or {}).get("channels") or [None])[0] or {}).get("alternatives") or [None]
            )[0]
            if isinstance(txt, dict):
                transcript = (txt.get("transcript") or "").strip()
            else:
                transcript = ""
        except Exception:
            transcript = ""

        return TextNormalizer.normalize(transcript, self.language)
