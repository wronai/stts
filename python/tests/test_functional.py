import os
import tempfile
import unittest
from pathlib import Path
import importlib.util
import importlib.machinery
from unittest.mock import patch


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


class TestFunctional(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory(prefix="stts_tests_")
        cls.stts = _load_stts_module(cls._tmp.name)
        cls.samples_dir = Path(__file__).resolve().parents[1] / "samples"

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_parse_args_basic(self):
        stts = self.stts
        args = [
            "--timeout",
            "8",
            "--vad-silence-ms",
            "1200",
            "--stt-provider",
            "vosk",
            "--stt-model",
            "pl",
            "--stt-file",
            "samples/cmd_ls.wav",
            "--stt-only",
        ]
        parsed = stts.parse_args(args)
        (stt_file, stt_only, stt_once, stt_stream_shell, stream_shell_cmd, setup, init, tts_provider, tts_voice, tts_stdin, tts_test, tts_test_text, install_piper, download_piper_voice, help_, dry_run, safe_mode, stream_cmd, fast_start, stt_gpu_layers, stt_provider, stt_model, timeout_s, vad_silence_ms, list_stt, list_tts, nlp2cmd_parallel, daemon_mode, nlp2cmd_url, nlp2cmd_timeout_s, daemon_log, daemon_no_execute, daemon_triggers, daemon_triggers_file, daemon_wake_word, rest) = parsed

        self.assertEqual(stt_file, "samples/cmd_ls.wav")
        self.assertTrue(stt_only)
        self.assertFalse(stt_once)
        self.assertEqual(stt_provider, "vosk")
        self.assertEqual(stt_model, "pl")
        self.assertEqual(timeout_s, 8.0)
        self.assertEqual(vad_silence_ms, 1200)
        self.assertEqual(rest, [])

    def test_yaml_roundtrip_simple(self):
        stts = self.stts
        data = {
            "stt_provider": "vosk",
            "stt_model": "small-pl",
            "timeout": 8,
            "vad_enabled": True,
            "mic_device": None,
            "tts_voice": "pl_PL-gosia-medium",
        }
        dumped = stts._dump_simple_yaml(data)
        parsed = stts._parse_simple_yaml(dumped)

        self.assertEqual(parsed.get("stt_provider"), "vosk")
        self.assertEqual(parsed.get("stt_model"), "small-pl")
        self.assertEqual(parsed.get("timeout"), 8)
        self.assertEqual(parsed.get("vad_enabled"), True)
        self.assertIsNone(parsed.get("mic_device"))
        self.assertEqual(parsed.get("tts_voice"), "pl_PL-gosia-medium")

    def test_wake_word_matching(self):
        stts = self.stts
        matched, remaining = stts.check_wake_word("hejken ls")
        self.assertTrue(matched)
        self.assertEqual(remaining, "ls")

        matched2, remaining2 = stts.check_wake_word("hej ken, proszę ls")
        self.assertTrue(matched2)
        self.assertIn("ls", remaining2)

    def test_generate_wake_word_variants_contains_original(self):
        stts = self.stts
        vars_ = stts.generate_wake_word_variants("hejken", max_variants=24)
        self.assertTrue(any(v.lower() == "hejken" for v in vars_))
        self.assertLessEqual(len(vars_), 24)

    def test_command_safety_helpers(self):
        stts = self.stts
        dangerous, _ = stts.is_dangerous_command("rm -rf /")
        self.assertTrue(dangerous)

        self.assertTrue(stts.is_sql_command("SELECT * FROM users"))
        self.assertFalse(stts.is_sql_command("ls -la"))

    def test_analyze_wav_sample(self):
        stts = self.stts
        wav = self.samples_dir / "cmd_echo_hello.wav"
        self.assertTrue(wav.exists())
        diag = stts.analyze_wav(str(wav))
        self.assertTrue(diag.get("ok"))
        self.assertEqual(diag.get("channels"), 1)
        self.assertIn("duration_s", diag)

    def test_nlp2cmd_translate_ignores_attempting(self):
        stts = self.stts

        old_enabled = os.environ.get("STTS_NLP2CMD_ENABLED")
        os.environ["STTS_NLP2CMD_ENABLED"] = "1"
        try:
            fake = type("R", (), {"stdout": "Attempting something\nls -la\n", "stderr": "", "returncode": 0})()
            with patch.object(stts.subprocess, "run", return_value=fake):
                cmd = stts.nlp2cmd_translate("lista folderów", config={}, force=False)
                self.assertEqual(cmd, "ls -la")

            fake2 = type("R", (), {"stdout": "Attempting something\n", "stderr": "", "returncode": 0})()
            with patch.object(stts.subprocess, "run", return_value=fake2):
                cmd2 = stts.nlp2cmd_translate("folderów", config={}, force=False)
                self.assertIsNone(cmd2)
        finally:
            if old_enabled is None:
                os.environ.pop("STTS_NLP2CMD_ENABLED", None)
            else:
                os.environ["STTS_NLP2CMD_ENABLED"] = old_enabled

    def test_looks_like_natural_language_heuristic(self):
        stts = self.stts
        self.assertTrue(stts._looks_like_natural_language("lista folderów"))
        self.assertFalse(stts._looks_like_natural_language("ls"))
        self.assertFalse(stts._looks_like_natural_language("/bin/ls -la"))
        self.assertFalse(stts._looks_like_natural_language("./script.sh"))


if __name__ == "__main__":
    unittest.main()
