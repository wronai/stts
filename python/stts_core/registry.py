from __future__ import annotations

from typing import Iterable, Tuple, Type

from stts_core.providers import STTProvider, TTSProvider


def build_stt_providers(items: Iterable[Tuple[str, Type[STTProvider]]]):
    return {k: v for k, v in items}


def build_tts_providers(items: Iterable[Tuple[str, Type[TTSProvider]]]):
    return {k: v for k, v in items}
