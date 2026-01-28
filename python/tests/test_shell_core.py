import os
import tempfile
import unittest
from pathlib import Path

from stts_core.shell import VoiceShell


class _ReadlineStub:
    def read_history_file(self, _path: str) -> None:
        return None

    def write_history_file(self, _path: str) -> None:
        return None


class _ColorsStub:
    RED = ""
    GREEN = ""
    YELLOW = ""
    MAGENTA = ""
    CYAN = ""
    BLUE = ""
    BOLD = ""
    NC = ""


class _DepsStub:
    def __init__(self, history_file: Path):
        self.HISTORY_FILE = history_file
        self.readline = _ReadlineStub()
        self.Colors = _ColorsStub
        self.STT_PROVIDERS = {}
        self.TTS_PROVIDERS = {}

    def cprint(self, _color: str, _text: str, end: str = "\n") -> None:
        return None

    def detect_system(self, fast: bool = True):
        class _Info:
            os_name = "linux"

        return _Info()

    def _ts(self) -> str:
        return "00:00:00"

    def analyze_wav(self, _path: str) -> dict:
        return {"ok": False}

    def save_config(self, _config: dict) -> None:
        return None


class TestVoiceShellCore(unittest.TestCase):
    def test_transcribe_mock_sidecar(self):
        old = os.environ.get("STTS_MOCK_STT")
        os.environ["STTS_MOCK_STT"] = "1"
        try:
            with tempfile.TemporaryDirectory(prefix="stts_shell_core_") as td:
                wav_path = Path(td) / "sample.wav"
                wav_path.write_bytes(b"")
                (Path(str(wav_path) + ".txt")).write_text("echo hello", encoding="utf-8")

                deps = _DepsStub(history_file=Path(td) / "history.txt")
                shell = VoiceShell(config={}, deps=deps)

                self.assertEqual(shell.transcribe(str(wav_path)), "echo hello")
        finally:
            if old is None:
                os.environ.pop("STTS_MOCK_STT", None)
            else:
                os.environ["STTS_MOCK_STT"] = old

    def test_listen_with_stt_file_uses_transcribe(self):
        old = os.environ.get("STTS_MOCK_STT")
        os.environ["STTS_MOCK_STT"] = "1"
        try:
            with tempfile.TemporaryDirectory(prefix="stts_shell_core_") as td:
                wav_path = Path(td) / "sample.wav"
                wav_path.write_bytes(b"")
                (Path(str(wav_path) + ".txt")).write_text("ls -la", encoding="utf-8")

                deps = _DepsStub(history_file=Path(td) / "history.txt")
                shell = VoiceShell(config={}, deps=deps)

                self.assertEqual(shell.listen(stt_file=str(wav_path)), "ls -la")
        finally:
            if old is None:
                os.environ.pop("STTS_MOCK_STT", None)
            else:
                os.environ["STTS_MOCK_STT"] = old


if __name__ == "__main__":
    unittest.main()
