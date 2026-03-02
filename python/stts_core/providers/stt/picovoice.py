"""Picovoice STT Provider for STTS."""

from __future__ import annotations

import os
from typing import Optional

from stts_core.providers import STTProvider
from stts_core.shell_utils import cprint, Colors
from stts_core.text import TextNormalizer


class PicovoiceSTT(STTProvider):
    """Picovoice Leopard - ultra-lightweight STT for embedded."""

    name = "picovoice"
    description = "Offline, ultra-light STT (~5MB, Pi Zero compatible)"
    min_ram_gb = 0.1

    @classmethod
    def is_available(cls, info):
        try:
            import pvleopard
            return True, "pvleopard installed"
        except ImportError:
            return False, "pip install pvleopard"

    @classmethod
    def get_recommended_model(cls, info) -> Optional[str]:
        return None

    def transcribe(self, audio_path: str) -> str:
        try:
            import pvleopard
        except ImportError:
            cprint(Colors.RED, "❌ pvleopard not installed: pip install pvleopard")
            return ""

        access_key = os.environ.get("PICOVOICE_ACCESS_KEY", "").strip()
        if not access_key:
            cprint(Colors.RED, "❌ PICOVOICE_ACCESS_KEY not set")
            return ""

        try:
            leopard = pvleopard.create(access_key=access_key)
            transcript, _ = leopard.process_file(audio_path)
            leopard.delete()
            return TextNormalizer.normalize(transcript or "", self.language)
        except Exception as e:
            cprint(Colors.RED, f"❌ Picovoice STT error: {e}")
            return ""
