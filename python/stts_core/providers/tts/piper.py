"""Piper TTS Provider for STTS."""

from __future__ import annotations

import os
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

from stts_core.providers import TTSProvider
from stts_core.config import MODELS_DIR, BIN_DIR
from stts_core.download_utils import _download_progress
from stts_core.shell_utils import cprint, Colors, detect_system, play_audio


class PiperTTS(TTSProvider):
    """Piper TTS - fast, local neural TTS with Polish voices."""

    name = "piper"

    @staticmethod
    def find_piper_bin() -> Optional[str]:
        p = shutil.which("piper")
        if p:
            return p
        for cand in (BIN_DIR / "piper", BIN_DIR / "piper" / "piper"):
            try:
                if cand.exists() and cand.is_file():
                    return str(cand)
            except Exception:
                continue
        return None

    @staticmethod
    def _piper_asset_name(info) -> Optional[str]:
        if info.os_name != "linux":
            return None
        arch = (info.arch or "").lower()
        if arch in ("x86_64", "amd64"):
            return "piper_linux_x86_64.tar.gz"
        if arch in ("aarch64", "arm64"):
            return "piper_linux_aarch64.tar.gz"
        if arch in ("armv7l",):
            return "piper_linux_armv7l.tar.gz"
        return None

    @classmethod
    def install_local(cls, info, release_tag: str) -> bool:
        asset = cls._piper_asset_name(info)
        if not asset:
            cprint(Colors.YELLOW, f"⚠️  Unsupported platform: os={info.os_name} arch={info.arch}")
            return False
        url = f"https://github.com/rhasspy/piper/releases/download/{release_tag}/{asset}"
        BIN_DIR.mkdir(parents=True, exist_ok=True)

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(prefix="stts_piper_", suffix=".tar.gz", delete=False) as f:
                tmp_path = f.name
            cprint(Colors.YELLOW, f"📥 Downloading piper binary: {asset}")
            urllib.request.urlretrieve(url, tmp_path, _download_progress)
            print()

            def _safe_members(tar: tarfile.TarFile):
                for m in tar.getmembers():
                    p = m.name
                    if p.startswith("/") or ".." in p.split("/"):
                        continue
                    yield m

            with tarfile.open(tmp_path, "r:gz") as tar:
                tar.extractall(path=str(BIN_DIR), members=list(_safe_members(tar)))

            piper_bin = cls.find_piper_bin()
            if not piper_bin:
                cprint(Colors.YELLOW, "⚠️  piper downloaded but binary not found")
                return False
            try:
                os.chmod(piper_bin, 0o755)
            except Exception:
                pass
            cprint(Colors.GREEN, f"✅ Piper installed: {piper_bin}")
            return True
        except Exception as e:
            cprint(Colors.YELLOW, f"⚠️  Piper install failed: {e}")
            return False
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

    @staticmethod
    def _parse_voice_id(voice_id: str) -> Optional[Tuple[str, str, str, str]]:
        v = (voice_id or "").strip()
        if not v or "/" in v or v.endswith(".onnx"):
            return None
        parts = v.split("-")
        if len(parts) < 3:
            return None
        locale = parts[0]
        quality = parts[-1]
        speaker = "-".join(parts[1:-1])
        lang = locale.split("_")[0].lower() if "_" in locale else locale.lower()
        return lang, locale, speaker, quality

    @classmethod
    def download_voice(cls, voice_id: str, voice_version: str) -> bool:
        parsed = cls._parse_voice_id(voice_id)
        if not parsed:
            cprint(Colors.YELLOW, f"⚠️  Invalid voice id for piper: {voice_id}")
            return False
        lang, locale, speaker, quality = parsed
        base = f"https://huggingface.co/rhasspy/piper-voices/resolve/{voice_version}"
        model_url = f"{base}/{lang}/{locale}/{speaker}/{quality}/{voice_id}.onnx?download=true"
        cfg_url = f"{base}/{lang}/{locale}/{speaker}/{quality}/{voice_id}.onnx.json?download=true"

        out_dir = MODELS_DIR / "piper"
        out_dir.mkdir(parents=True, exist_ok=True)
        model_path = out_dir / f"{voice_id}.onnx"
        cfg_path = out_dir / f"{voice_id}.onnx.json"

        try:
            if not model_path.exists() or model_path.stat().st_size < 1024 * 1024:
                cprint(Colors.YELLOW, f"📥 Downloading piper voice model: {voice_id}")
                urllib.request.urlretrieve(model_url, str(model_path), _download_progress)
                print()
            if not cfg_path.exists() or cfg_path.stat().st_size < 100:
                cprint(Colors.YELLOW, f"📥 Downloading piper voice config: {voice_id}")
                urllib.request.urlretrieve(cfg_url, str(cfg_path), _download_progress)
                print()
            cprint(Colors.GREEN, f"✅ Piper voice ready: {model_path}")
            return True
        except Exception as e:
            cprint(Colors.YELLOW, f"⚠️  Piper voice download failed: {e}")
            return False

    @classmethod
    def is_available(cls, info):
        if cls.find_piper_bin():
            return True, "piper found"
        return False, "install piper (binary)"

    def _resolve_model(self) -> Optional[str]:
        v = (self.voice or "").strip()
        if not v:
            return None

        VOICE_ALIASES = {
            "pl": "pl_PL-gosia-medium",
            "en": "en_US-amy-medium",
            "de": "de_DE-thorsten-medium",
            "fr": "fr_FR-upmc-medium",
            "es": "es_ES-carlfm-medium",
        }
        if v in VOICE_ALIASES:
            v = VOICE_ALIASES[v]

        p = Path(v).expanduser()
        if p.exists() and p.is_file():
            cfg = Path(str(p) + ".json")
            if not cfg.exists():
                cprint(Colors.YELLOW, f"⚠️  Missing config file for piper: {cfg}")
                return None
            return str(p)
        p2 = MODELS_DIR / "piper" / f"{v}.onnx"
        if p2.exists():
            cfg = Path(str(p2) + ".json")
            if not cfg.exists():
                cprint(Colors.YELLOW, f"⚠️  Missing config file for piper: {cfg}")
                return None
            return str(p2)
        return None

    def speak(self, text: str) -> None:
        piper = self.find_piper_bin()
        cfg = self.config or {}
        if not piper and cfg.get("piper_auto_install", True):
            try:
                info = self.info or detect_system(fast=True)
                self.install_local(info, cfg.get("piper_release_tag", "2023.11.14-2"))
                piper = self.find_piper_bin()
            except Exception:
                piper = self.find_piper_bin()

        model = self._resolve_model()
        if not model and cfg.get("piper_auto_download", True):
            try:
                self.download_voice(self.voice, cfg.get("piper_voice_version", "v1.0.0"))
            except Exception:
                pass
            model = self._resolve_model()

        if not piper:
            cprint(Colors.YELLOW, "⚠️  Piper binary not found in PATH")
            return
        if not model:
            cprint(Colors.YELLOW, "⚠️  Piper model not set. Set tts_voice to .onnx path or name from ~/.config/stts-python/models/piper/")
            return
        try:
            with tempfile.NamedTemporaryFile(prefix="stts_piper_", suffix=".wav", delete=False) as f:
                out_path = f.name
            res = subprocess.run(
                [piper, "--model", model, "--output_file", out_path],
                input=text,
                text=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=60,
            )
            if getattr(res, "returncode", 0) != 0:
                cprint(Colors.YELLOW, f"⚠️  piper returncode={res.returncode}")
            play_audio(out_path)
            try:
                Path(out_path).unlink(missing_ok=True)
            except Exception:
                pass
        except Exception:
            return
