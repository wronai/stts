"""Tests for STT/TTS provider classes."""
import os
import tempfile
import unittest
from pathlib import Path
import importlib.util
import importlib.machinery


def _load_stts_module(config_dir: str):
    os.environ["STTS_CONFIG_DIR"] = config_dir
    os.environ["STTS_NLP2CMD_ENABLED"] = "0"
    os.environ.setdefault("STTS_AUTO_TTS", "0")
    stts_path = Path(__file__).resolve().parents[1] / "stts"
    loader = importlib.machinery.SourceFileLoader("stts_script", str(stts_path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class TestSTTProviders(unittest.TestCase):
    """Test STT provider classes."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory(prefix="stts_provider_tests_")
        cls.stts = _load_stts_module(cls._tmp.name)
        cls.samples_dir = Path(__file__).resolve().parents[1] / "samples"

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_stt_providers_registry(self):
        """All expected STT providers are registered."""
        stts = self.stts
        expected = ["whisper_cpp", "deepgram", "vosk", "coqui", "picovoice", "faster_whisper"]
        for name in expected:
            self.assertIn(name, stts.STT_PROVIDERS, f"Missing STT provider: {name}")

    def test_stt_provider_base_class(self):
        """STTProvider base class has required methods."""
        stts = self.stts
        self.assertTrue(hasattr(stts.STTProvider, "is_available"))
        self.assertTrue(hasattr(stts.STTProvider, "install"))
        self.assertTrue(hasattr(stts.STTProvider, "get_recommended_model"))
        self.assertTrue(hasattr(stts.STTProvider, "transcribe"))

    def test_whisper_cpp_provider_attributes(self):
        """WhisperCppSTT has correct attributes."""
        stts = self.stts
        cls = stts.WhisperCppSTT
        self.assertEqual(cls.name, "whisper.cpp")
        self.assertGreater(len(cls.models), 0)
        self.assertIn("tiny", [m[0] for m in cls.models])
        self.assertIn("base", [m[0] for m in cls.models])

    def test_vosk_provider_attributes(self):
        """VoskSTT has correct attributes."""
        stts = self.stts
        cls = stts.VoskSTT
        self.assertEqual(cls.name, "vosk")
        self.assertGreater(len(cls.models), 0)

    def test_faster_whisper_provider_attributes(self):
        """FasterWhisperSTT has correct attributes."""
        stts = self.stts
        cls = stts.FasterWhisperSTT
        self.assertEqual(cls.name, "faster_whisper")
        self.assertIn("tiny", [m[0] for m in cls.models])
        self.assertIn("distil-large-v3", [m[0] for m in cls.models])

    def test_faster_whisper_recommended_model(self):
        """FasterWhisperSTT recommends appropriate model based on RAM."""
        stts = self.stts

        class MockInfo:
            ram_gb = 2

        self.assertEqual(stts.FasterWhisperSTT.get_recommended_model(MockInfo()), "base")

        MockInfo.ram_gb = 16
        self.assertEqual(stts.FasterWhisperSTT.get_recommended_model(MockInfo()), "large-v3")

    def test_deepgram_provider_requires_key(self):
        """DeepgramSTT requires API key."""
        stts = self.stts
        cls = stts.DeepgramSTT

        # Clear key if set
        old_key = os.environ.pop("STTS_DEEPGRAM_KEY", None)
        try:
            info = stts.detect_system(fast=True)
            available, reason = cls.is_available(info)
            self.assertFalse(available)
            self.assertIn("STTS_DEEPGRAM_KEY", reason)
        finally:
            if old_key:
                os.environ["STTS_DEEPGRAM_KEY"] = old_key

    def test_mock_stt_with_sidecar(self):
        """STTS_MOCK_STT=1 uses sidecar .txt file."""
        stts = self.stts
        wav_file = self.samples_dir / "cmd_echo_hello.wav"
        txt_file = self.samples_dir / "cmd_echo_hello.wav.txt"

        self.assertTrue(wav_file.exists())
        self.assertTrue(txt_file.exists())

        os.environ["STTS_MOCK_STT"] = "1"
        try:
            config = {"stt_provider": "whisper_cpp", "language": "pl"}
            shell = stts.VoiceShell(config)
            result = shell.transcribe(str(wav_file))
            expected = txt_file.read_text().strip()
            self.assertEqual(result, expected)
        finally:
            os.environ.pop("STTS_MOCK_STT", None)


class TestTTSProviders(unittest.TestCase):
    """Test TTS provider classes."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory(prefix="stts_provider_tests_")
        cls.stts = _load_stts_module(cls._tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_tts_providers_registry(self):
        """All expected TTS providers are registered."""
        stts = self.stts
        expected = ["espeak", "piper", "spd-say", "say", "flite", "coqui-tts", "festival", "rhvoice", "kokoro"]
        for name in expected:
            self.assertIn(name, stts.TTS_PROVIDERS, f"Missing TTS provider: {name}")

    def test_tts_provider_base_class(self):
        """TTSProvider base class has required methods."""
        stts = self.stts
        self.assertTrue(hasattr(stts.TTSProvider, "is_available"))
        self.assertTrue(hasattr(stts.TTSProvider, "speak"))

    def test_espeak_provider_attributes(self):
        """EspeakTTS has correct attributes."""
        stts = self.stts
        cls = stts.EspeakTTS
        self.assertEqual(cls.name, "espeak")

    def test_piper_provider_attributes(self):
        """PiperTTS has correct attributes."""
        stts = self.stts
        cls = stts.PiperTTS
        self.assertEqual(cls.name, "piper")

    def test_rhvoice_provider_attributes(self):
        """RHVoiceTTS has correct attributes."""
        stts = self.stts
        cls = stts.RHVoiceTTS
        self.assertEqual(cls.name, "rhvoice")


class TestProviderDetection(unittest.TestCase):
    """Test provider availability detection."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory(prefix="stts_provider_tests_")
        cls.stts = _load_stts_module(cls._tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_detect_system_returns_info(self):
        """detect_system returns SystemInfo object."""
        stts = self.stts
        info = stts.detect_system(fast=True)
        self.assertIsInstance(info, stts.SystemInfo)
        self.assertIsNotNone(info.os_name)

    def test_provider_is_available_returns_tuple(self):
        """Provider.is_available returns (bool, str) tuple."""
        stts = self.stts
        info = stts.detect_system(fast=True)

        for name, cls in stts.STT_PROVIDERS.items():
            result = cls.is_available(info)
            self.assertIsInstance(result, tuple, f"{name} is_available should return tuple")
            self.assertEqual(len(result), 2, f"{name} is_available should return 2 elements")
            self.assertIsInstance(result[0], bool, f"{name} is_available[0] should be bool")
            self.assertIsInstance(result[1], str, f"{name} is_available[1] should be str")

        for name, cls in stts.TTS_PROVIDERS.items():
            result = cls.is_available(info)
            self.assertIsInstance(result, tuple, f"{name} is_available should return tuple")
            self.assertEqual(len(result), 2, f"{name} is_available should return 2 elements")


if __name__ == "__main__":
    unittest.main()
