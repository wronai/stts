import os
import tempfile
import unittest
import subprocess
from pathlib import Path


class TestE2ECLI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.python_dir = Path(__file__).resolve().parents[1]
        cls.stts_path = cls.python_dir / "stts"
        cls.samples_dir = cls.python_dir / "samples"

        assert cls.stts_path.exists()
        assert (cls.samples_dir / "cmd_echo_hello.wav").exists()

    def _run(self, args, *, cwd=None, extra_env=None, timeout=30):
        env = os.environ.copy()
        env["STTS_MOCK_STT"] = "1"
        env["STTS_AUTO_TTS"] = "0"
        env["STTS_NLP2CMD_ENABLED"] = env.get("STTS_NLP2CMD_ENABLED", "0")

        with tempfile.TemporaryDirectory(prefix="stts_e2e_cfg_") as cfg:
            env["STTS_CONFIG_DIR"] = cfg
            if extra_env:
                env.update({k: str(v) for k, v in extra_env.items()})

            res = subprocess.run(
                ["python3", str(self.stts_path), *args],
                cwd=str(cwd or self.python_dir),
                env=env,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return res

    def test_stt_only_mock_echo_hello(self):
        wav = self.samples_dir / "cmd_echo_hello.wav"
        res = self._run(["--stt-file", str(wav), "--stt-only"])
        self.assertEqual(res.returncode, 0)
        self.assertIn("echo hello", res.stdout)

    def test_stt_once_mock(self):
        wav = self.samples_dir / "cmd_echo_hello.wav"
        res = self._run(["--stt-file", str(wav), "--stt-once"])
        self.assertEqual(res.returncode, 0)
        self.assertIn("echo hello", res.stdout)

    def test_execute_from_stt_file_mock(self):
        wav = self.samples_dir / "cmd_echo_hello.wav"
        res = self._run(["--stt-file", str(wav)])
        self.assertEqual(res.returncode, 0)
        self.assertIn("hello", res.stdout)

    def test_placeholder_dry_run(self):
        wav = self.samples_dir / "cmd_echo_hello.wav"
        res = self._run(["--stt-file", str(wav), "--dry-run", "echo", "{STT}"])
        self.assertEqual(res.returncode, 0)
        self.assertIn("echo hello", res.stdout)

    def test_execute_ls_from_stt_file_mock(self):
        wav = self.samples_dir / "cmd_ls.wav"
        res = self._run(["--stt-file", str(wav)])
        self.assertEqual(res.returncode, 0)
        self.assertIn("README.md", res.stdout)

    def test_stream_shell_dry_run(self):
        wav = self.samples_dir / "cmd_echo_hello.wav"
        res = self._run(
            [
                "--stt-file",
                str(wav),
                "--stt-stream-shell",
                "--cmd",
                "echo '{STT_STREAM}'",
                "--dry-run",
            ]
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("echo hello", res.stdout)


if __name__ == "__main__":
    unittest.main()
