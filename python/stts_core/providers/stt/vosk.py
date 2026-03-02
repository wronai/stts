"""Vosk STT Provider for STTS."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple

from stts_core.providers import STTProvider
from stts_core.config import MODELS_DIR
from stts_core.download_utils import _download_progress
from stts_core.shell_utils import cprint, Colors
from stts_core.text import TextNormalizer


class VoskSTT(STTProvider):
    """Offline, fast, lightweight STT (good for RPi)."""

    name = "vosk"
    description = "Offline, fast, lightweight STT (good for RPi)"
    min_ram_gb = 0.5
    models = [
        ("small-pl", "vosk-model-small-pl-0.22", 0.05),
        ("pl", "vosk-model-small-pl-0.22", 0.05),
        ("pl-full", "vosk-model-pl-0.22", 0.2),
        ("pl-0.22", "vosk-model-pl-0.22", 0.2),
        ("small-en", "vosk-model-small-en-us-0.15", 0.04),
    ]

    @classmethod
    def is_available(cls, info):
        try:
            import vosk
            vosk.SetLogLevel(-1)
        except ImportError:
            return False, "pip install vosk"
        # Check if any model exists
        vosk_dir = MODELS_DIR / "vosk"
        if vosk_dir.exists():
            models = list(vosk_dir.glob("vosk-model-*"))
            if models:
                return True, f"vosk + {len(models)} model(s)"
        return False, "vosk installed, no models (make stt-vosk-pl)"

    @classmethod
    def install(cls, info) -> bool:
        try:
            res = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-U", "vosk"],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if res.returncode == 0:
                return True
        except Exception:
            pass

        try:
            res = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-U", "--user", "vosk"],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if res.returncode == 0:
                return True
        except Exception:
            pass
        return False

    @classmethod
    def download_model(cls, model_name: str) -> Optional[Path]:
        name = (model_name or "").strip() or "small-pl"
        if name in ("pl", "pl_PL"):
            name = "small-pl"
        if name in ("pl-full", "pl_full"):
            name = "pl-0.22"

        url = None
        out_dir = MODELS_DIR / "vosk"
        out_dir.mkdir(parents=True, exist_ok=True)

        if name in ("small-pl", "pl-small"):
            url = "https://alphacephei.com/vosk/models/vosk-model-small-pl-0.22.zip"
        elif name in ("pl-0.22", "pl"):
            url = "https://alphacephei.com/vosk/models/vosk-model-pl-0.22.zip"
        elif name in ("small-en", "en"):
            url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
        else:
            mappings = {
                "vosk-model-small-pl-0.22": "https://alphacephei.com/vosk/models/vosk-model-small-pl-0.22.zip",
                "vosk-model-pl-0.22": "https://alphacephei.com/vosk/models/vosk-model-pl-0.22.zip",
                "vosk-model-small-en-us-0.15": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
            }
            url = mappings.get(name)

        if not url:
            return None

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(prefix="stts_vosk_", suffix=".zip", delete=False) as f:
                tmp_path = f.name
            urllib.request.urlretrieve(url, tmp_path, _download_progress)
            print()

            with zipfile.ZipFile(tmp_path, "r") as z:
                for member in z.infolist():
                    p = member.filename
                    if p.startswith("/") or ".." in p.split("/"):
                        continue
                    z.extract(member, path=str(out_dir))

            # Return the first extracted model dir
            extracted = list(out_dir.glob("vosk-model-*/"))
            if extracted:
                return extracted[0]
            extracted2 = list(out_dir.glob("vosk-model-*"))
            if extracted2:
                return extracted2[0]
        except Exception:
            return None
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
        return None

    @classmethod
    def get_recommended_model(cls, info) -> Optional[str]:
        return "small-pl"

    def _find_model_path(self) -> Optional[Path]:
        """Find vosk model directory."""
        vosk_dir = MODELS_DIR / "vosk"
        if not vosk_dir.exists():
            return None

        # If model is a full path
        if self.model and Path(self.model).exists():
            return Path(self.model)

        # Map short names to directory names
        model_name = self.model or "small-pl"
        mappings = {
            "small-pl": "vosk-model-small-pl-0.22",
            "pl": "vosk-model-small-pl-0.22",
            "pl-small": "vosk-model-small-pl-0.22",
            "pl-full": "vosk-model-pl-0.22",
            "pl-0.22": "vosk-model-pl-0.22",
            "small-en": "vosk-model-small-en-us-0.15",
        }
        dir_name = mappings.get(model_name, model_name)

        # Try exact match
        model_path = vosk_dir / dir_name
        if model_path.exists():
            return model_path

        # Try glob
        matches = list(vosk_dir.glob(f"*{model_name}*"))
        if matches:
            return matches[0]

        # Fallback to first available
        models = list(vosk_dir.glob("vosk-model-*"))
        if models:
            return models[0]

        return None

    def transcribe(self, audio_path: str) -> str:
        try:
            import vosk
            vosk.SetLogLevel(-1)
        except ImportError:
            cprint(Colors.RED, "❌ vosk not installed: pip install vosk")
            return ""

        model_path = self._find_model_path()
        if not model_path:
            cprint(Colors.RED, "❌ Vosk model not found. Run: make stt-vosk-pl")
            return ""

        try:
            import wave
            model = vosk.Model(str(model_path))

            def _decode_with_grammar(grammar: str) -> Tuple[str, str]:
                wf = wave.open(audio_path, "rb")
                if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
                    wf.close()
                    cprint(Colors.YELLOW, "⚠️ Audio must be mono 16-bit WAV")
                    return "", ""

                def _run_recognizer(r) -> Tuple[str, str]:
                    while True:
                        data = wf.readframes(4000)
                        if len(data) == 0:
                            break
                        r.AcceptWaveform(data)
                    fj = r.FinalResult()
                    try:
                        jj = json.loads(fj)
                        tt = (jj.get("text") or "").strip()
                    except Exception:
                        tt = ""
                    return fj, tt

                if grammar:
                    try:
                        rec = vosk.KaldiRecognizer(model, wf.getframerate(), grammar)
                    except TypeError:
                        rec = vosk.KaldiRecognizer(model, wf.getframerate())
                        try:
                            rec.SetGrammar(grammar)
                        except Exception:
                            pass
                else:
                    rec = vosk.KaldiRecognizer(model, wf.getframerate())
                rec.SetWords(False)

                final_json, transcript = _run_recognizer(rec)
                if (not transcript) and grammar:
                    try:
                        wf.rewind()
                        rec2 = vosk.KaldiRecognizer(model, wf.getframerate())
                        rec2.SetWords(False)
                        final_json2, transcript2 = _run_recognizer(rec2)
                        if transcript2:
                            cprint(Colors.YELLOW, "⚠️ Vosk: grammar returned empty, retry without grammar")
                            final_json = final_json2
                            transcript = transcript2
                    except Exception:
                        pass

                wf.close()
                return transcript, final_json

            grammar_src = (
                (self.config.get("stt_vosk_grammar") if isinstance(self.config, dict) else None)
                or os.environ.get("STTS_VOSK_GRAMMAR_JSON", "")
            )
            grammar_src = str(grammar_src or "").strip()
            if grammar_src and Path(grammar_src).exists():
                try:
                    grammar_src = Path(grammar_src).read_text(encoding="utf-8")
                except Exception:
                    grammar_src = ""
            grammar_json = ""
            if grammar_src:
                try:
                    j = json.loads(grammar_src)
                    if isinstance(j, list):
                        grammar_json = json.dumps(j)
                    elif isinstance(j, dict):
                        phrases: List[str] = []
                        for v in j.values():
                            if not isinstance(v, list):
                                continue
                            for alt in v:
                                if isinstance(alt, list):
                                    phrase = " ".join(str(x).strip() for x in alt if str(x).strip())
                                    if phrase:
                                        phrases.append(phrase)
                                elif isinstance(alt, str) and alt.strip():
                                    phrases.append(alt.strip())
                        if phrases:
                            grammar_json = json.dumps(sorted(set(phrases)))
                except Exception:
                    grammar_json = ""

            transcript, final_json = _decode_with_grammar(grammar_json)
            if (not transcript) and grammar_json:
                transcript, final_json = _decode_with_grammar("")

            debug = (os.environ.get("STTS_DEBUG_STT") == "1") or (os.environ.get("STTS_DEBUG_VOSK") == "1")
            if debug and (not transcript):
                try:
                    cprint(
                        Colors.MAGENTA,
                        f"[stts] vosk empty result: model={model_path}",
                    )
                    cprint(Colors.MAGENTA, f"[stts] vosk FinalResult: {final_json}")
                except Exception:
                    pass

            return TextNormalizer.normalize(transcript, self.language)

        except Exception as e:
            cprint(Colors.RED, f"❌ Vosk error: {e}")
            return ""
