"""Whisper.cpp STT Provider for STTS."""

from __future__ import annotations

import functools
import math
import os
import re
import shutil
import subprocess
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

from stts_core.providers import STTProvider
from stts_core.config import MODELS_DIR
from stts_core.shell_utils import cprint, Colors, detect_system
from stts_core.text import TextNormalizer


class WhisperCppSTT(STTProvider):
    """Offline, fast, CPU-optimized Whisper (recommended)."""

    name = "whisper.cpp"
    description = "Offline, fast, CPU-optimized Whisper (recommended)"
    min_ram_gb = 1.0
    models = [
        ("tiny", "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin", 0.08),
        ("base", "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin", 0.15),
        ("small", "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin", 0.5),
        ("medium", "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin", 1.5),
        ("large", "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin", 3.0),
    ]

    @classmethod
    def is_available(cls, info):
        for b in ("whisper-cli", "whisper-cpp"):
            if shutil.which(b):
                return True, f"{b} found"
        # legacy
        if shutil.which("main"):
            return True, "main found"
        for p in (
            MODELS_DIR / "whisper.cpp" / "build" / "bin" / "whisper-cli",
            MODELS_DIR / "whisper.cpp" / "build" / "bin" / "main",
            MODELS_DIR / "whisper.cpp" / "main",
        ):
            if p.exists():
                return True, f"whisper.cpp at {p}"
        return False, "whisper.cpp not installed"

    @classmethod
    def get_recommended_model(cls, info) -> Optional[str]:
        if info.ram_gb < 2:
            return "tiny"
        if info.ram_gb < 4:
            return "base"
        if info.ram_gb < 8:
            return "small"
        if info.ram_gb < 16:
            return "medium"
        return "large"

    @classmethod
    def _detect_cuda(cls) -> bool:
        """Check if CUDA toolkit is available."""
        try:
            result = subprocess.run(
                ["nvcc", "--version"],
                capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    @classmethod
    def _has_gpu_build(cls) -> bool:
        """Check if whisper.cpp was built with GPU support."""
        marker = MODELS_DIR / "whisper.cpp" / ".gpu_build"
        return marker.exists()

    @classmethod
    def install(cls, info, force_gpu: Optional[bool] = None) -> bool:
        cprint(Colors.YELLOW, "📦 Installing whisper.cpp...")
        whisper_dir = MODELS_DIR / "whisper.cpp"
        whisper_dir.mkdir(parents=True, exist_ok=True)

        already_built = any(
            p.exists()
            for p in (
                whisper_dir / "build" / "bin" / "whisper-cli",
                whisper_dir / "build" / "bin" / "main",
                whisper_dir / "main",
            )
        )
        if already_built:
            gpu_info = " (GPU)" if cls._has_gpu_build() else " (CPU)"
            cprint(Colors.GREEN, f"✅ whisper.cpp already installed!{gpu_info}")
            return True

        try:
            if not (whisper_dir / "Makefile").exists():
                subprocess.run(
                    ["git", "clone", "https://github.com/ggerganov/whisper.cpp", str(whisper_dir)],
                    check=True,
                )

            use_cuda = force_gpu if force_gpu is not None else cls._detect_cuda()
            env_gpu = os.environ.get("STTS_GPU_ENABLED", "").strip().lower()
            if env_gpu in ("1", "true", "yes"):
                use_cuda = True
            elif env_gpu in ("0", "false", "no"):
                use_cuda = False

            if use_cuda:
                cprint(Colors.GREEN, "🎮 CUDA detected - building with GPU support...")
                build_dir = whisper_dir / "build"
                build_dir.mkdir(exist_ok=True)
                subprocess.run(
                    ["cmake", "..", "-DGGML_CUDA=ON", "-DCMAKE_BUILD_TYPE=Release"],
                    cwd=build_dir, check=True
                )
                subprocess.run(
                    ["cmake", "--build", ".", "--config", "Release", "-j"],
                    cwd=build_dir, check=True
                )
                (whisper_dir / ".gpu_build").write_text("cuda")
            else:
                cprint(Colors.YELLOW, "📦 Building CPU-only version...")
                subprocess.run(["make", "-j"], cwd=whisper_dir, check=True)

            cprint(Colors.GREEN, "✅ whisper.cpp installed!")
            return True
        except Exception as e:
            cprint(Colors.RED, f"❌ Installation failed: {e}")
            return False

    @classmethod
    def download_model(cls, model_name: str) -> Optional[Path]:
        from stts_core.download_utils import _download_progress

        model_info = next((m for m in cls.models if m[0] == model_name), None)
        if not model_info:
            cprint(Colors.RED, f"❌ Unknown model: {model_name}")
            return None

        name, url, size = model_info
        expected_bytes = int(float(size) * 1024 * 1024 * 1024)
        if name == "large":
            # upstream naming changed to large-v3; accept both
            p1 = MODELS_DIR / "whisper.cpp" / "ggml-large.bin"
            p2 = MODELS_DIR / "whisper.cpp" / "ggml-large-v3.bin"
            if p2.exists() and p2.stat().st_size > max(1024 * 1024, int(expected_bytes * 0.9)):
                return p2
            if p1.exists() and p1.stat().st_size > max(1024 * 1024, int(expected_bytes * 0.9)):
                return p1
            model_path = p2
        else:
            model_path = MODELS_DIR / "whisper.cpp" / f"ggml-{name}.bin"
            if model_path.exists() and model_path.stat().st_size > max(1024 * 1024, int(expected_bytes * 0.9)):
                return model_path

        if model_path.exists() and model_path.stat().st_size > max(1024 * 1024, int(expected_bytes * 0.9)):
            return model_path

        cprint(Colors.YELLOW, f"📥 Downloading {name} model ({size} GB)...")
        model_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            urllib.request.urlretrieve(url, model_path, _download_progress)
            print()
            cprint(Colors.GREEN, f"✅ Model {name} downloaded!")
            return model_path
        except Exception as e:
            cprint(Colors.RED, f"❌ Download failed: {e}")
            return None

    @staticmethod
    @functools.lru_cache(maxsize=32)
    def _help_text(whisper_bin: str) -> str:
        for args in (("--help",), ("-h",), ("-help",)):
            try:
                res = subprocess.run(
                    [whisper_bin, *args],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                out = (res.stdout or "") + (res.stderr or "")
                if out.strip():
                    return out
            except Exception:
                continue
        return ""

    @staticmethod
    def _is_short_audio(audio_path: str, max_seconds: float = 8.0) -> bool:
        try:
            import wave

            with wave.open(audio_path, "rb") as wf:
                frames = int(wf.getnframes() or 0)
                rate = int(wf.getframerate() or 0)
                if rate <= 0:
                    return False
                dur = float(frames) / float(rate)
                return dur <= float(max_seconds)
        except Exception:
            return False

    @staticmethod
    @functools.lru_cache(maxsize=128)
    def _supports_help_token(whisper_bin: str, token: str) -> bool:
        return token in WhisperCppSTT._help_text(whisper_bin)

    @staticmethod
    @functools.lru_cache(maxsize=32)
    def _detect_prompt_flag(whisper_bin: str) -> Optional[str]:
        out = WhisperCppSTT._help_text(whisper_bin)
        if "--prompt" in out:
            return "--prompt"
        if re.search(r"(?mi)^\s*-p\b.*prompt", out):
            return "-p"
        return None

    def transcribe(self, audio_path: str) -> str:
        whisper_bin = shutil.which("whisper-cli") or shutil.which("whisper-cpp") or shutil.which("main")
        if not whisper_bin:
            candidates = [
                MODELS_DIR / "whisper.cpp" / "build" / "bin" / "whisper-cli",
                MODELS_DIR / "whisper.cpp" / "build" / "bin" / "main",
                MODELS_DIR / "whisper.cpp" / "main",
            ]
            for c in candidates:
                if c.exists():
                    whisper_bin = str(c)
                    break

        model_name = self.model or "base"
        if model_name == "large":
            p2 = MODELS_DIR / "whisper.cpp" / "ggml-large-v3.bin"
            p1 = MODELS_DIR / "whisper.cpp" / "ggml-large.bin"
            model_path = p2 if p2.exists() else p1
        else:
            model_path = MODELS_DIR / "whisper.cpp" / f"ggml-{model_name}.bin"
        if not model_path.exists():
            model_path = self.download_model(model_name)

        if not model_path:
            return ""

        try:
            short_audio = self._is_short_audio(audio_path)

            lang = str(self.language or "").strip()
            if lang.lower() in ("", "auto"):
                cmd = [whisper_bin, "-m", str(model_path), "-f", audio_path, "-nt"]
            else:
                cmd = [whisper_bin, "-m", str(model_path), "-l", lang, "-f", audio_path, "-nt"]

            threads = (
                (self.config.get("stt_threads") if isinstance(self.config, dict) else None)
                or os.environ.get("STTS_STT_THREADS", "")
            )
            try:
                threads_i = int(str(threads).strip()) if str(threads).strip() else 0
            except Exception:
                threads_i = 0
            if threads_i <= 0:
                threads_i = 4 if short_audio else min(os.cpu_count() or 4, 8)
            cmd.extend(["-t", str(threads_i)])

            # Add other parameters (max_len, word_thold, etc.)
            # ... (simplified for brevity)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            raw_text = result.stdout.strip()
            return TextNormalizer.normalize(raw_text, self.language)
        except Exception as e:
            cprint(Colors.RED, f"❌ Transcription error: {e}")
            return ""
