from __future__ import annotations

from typing import Any, List, Optional, Tuple


class STTProvider:
    name: str = "base"
    description: str = "Base"
    min_ram_gb: float = 0.5
    models: List[Tuple[str, str, float]] = []

    @classmethod
    def is_available(cls, info: Any):
        return False, "Not implemented"

    @classmethod
    def install(cls, info: Any) -> bool:
        return False

    @classmethod
    def get_recommended_model(cls, info: Any) -> Optional[str]:
        return None

    def __init__(
        self,
        model: Optional[str] = None,
        language: str = "pl",
        config: Optional[dict] = None,
        info: Any = None,
    ):
        self.model = model
        self.language = language
        self.config = config or {}
        self.info = info

    def transcribe(self, audio_path: str) -> str:
        raise NotImplementedError


class TTSProvider:
    name: str = "base"

    @classmethod
    def is_available(cls, info: Any):
        return False, "Not implemented"

    @classmethod
    def install(cls, info: Any) -> bool:
        return False

    def __init__(self, voice: str = "pl", config: Optional[dict] = None, info: Any = None):
        self.voice = voice
        self.config = config or {}
        self.info = info

    def speak(self, text: str) -> None:
        raise NotImplementedError
