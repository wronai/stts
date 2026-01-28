from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional


_CONFIG_DIR_ENV = os.environ.get("STTS_CONFIG_DIR")
CONFIG_DIR = (
    Path(_CONFIG_DIR_ENV).expanduser()
    if _CONFIG_DIR_ENV
    else (Path.home() / ".config" / "stts-python")
)

CONFIG_FILE_JSON = CONFIG_DIR / "config.json"
CONFIG_FILE_YAML = CONFIG_DIR / "config.yaml"
CONFIG_FILE_YML = CONFIG_DIR / "config.yml"

MODELS_DIR = CONFIG_DIR / "models"
BIN_DIR = CONFIG_DIR / "bin"
HISTORY_FILE = CONFIG_DIR / "history"

DEFAULT_CONFIG: dict[str, Any] = {
    "stt_provider": None,
    "tts_provider": None,
    "stt_model": None,
    "stt_gpu_layers": 0,
    "tts_voice": "pl",
    "language": "pl",
    "timeout": 5,
    "auto_tts": True,
    "stream_cmd": False,
    "fast_start": True,
    "mic_device": None,
    "speaker_device": None,
    "audio_auto_switch": True,
    "prompt_voice_first": True,
    "startup_tts": True,
    "vad_enabled": True,
    "vad_silence_ms": 800,
    "vad_threshold_db": -42,
    "safe_mode": False,
    "vosk_auto_install": True,
    "vosk_auto_download": True,
    "piper_auto_install": True,
    "piper_auto_download": True,
    "piper_release_tag": "2023.11.14-2",
    "piper_voice_version": "v1.0.0",
    "nlp2cmd_parallel": False,
}


def normalize_config_format(v: Optional[str]) -> Optional[str]:
    if not v:
        return None
    s = v.strip().lower()
    if s in ("yaml", "yml"):
        return "yaml"
    if s in ("json",):
        return "json"
    return None


def get_config_file_for_load() -> Optional[Path]:
    fmt = normalize_config_format(os.environ.get("STTS_CONFIG_FORMAT"))
    if fmt == "yaml":
        if CONFIG_FILE_YAML.exists():
            return CONFIG_FILE_YAML
        if CONFIG_FILE_YML.exists():
            return CONFIG_FILE_YML
        return CONFIG_FILE_YAML
    if fmt == "json":
        return CONFIG_FILE_JSON

    if CONFIG_FILE_YAML.exists():
        return CONFIG_FILE_YAML
    if CONFIG_FILE_YML.exists():
        return CONFIG_FILE_YML
    if CONFIG_FILE_JSON.exists():
        return CONFIG_FILE_JSON
    return CONFIG_FILE_JSON


def get_config_file_for_save() -> Path:
    fmt = normalize_config_format(os.environ.get("STTS_CONFIG_FORMAT"))
    if fmt == "yaml":
        if CONFIG_FILE_YML.exists() and not CONFIG_FILE_YAML.exists():
            return CONFIG_FILE_YML
        return CONFIG_FILE_YAML
    if fmt == "json":
        return CONFIG_FILE_JSON

    if CONFIG_FILE_YAML.exists():
        return CONFIG_FILE_YAML
    if CONFIG_FILE_YML.exists():
        return CONFIG_FILE_YML
    if CONFIG_FILE_JSON.exists():
        return CONFIG_FILE_JSON
    return CONFIG_FILE_JSON


def parse_simple_yaml(text: str) -> dict:
    out: dict = {}
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        key = k.strip()
        if not key:
            continue
        val_s = v.strip()
        if not val_s or val_s in ("null", "~"):
            out[key] = None
            continue

        if (val_s.startswith('"') and val_s.endswith('"')) or (
            val_s.startswith("'") and val_s.endswith("'")
        ):
            out[key] = val_s[1:-1]
            continue

        low = val_s.lower()
        if low in ("true", "yes", "y", "on"):
            out[key] = True
            continue
        if low in ("false", "no", "n", "off"):
            out[key] = False
            continue

        try:
            if any(ch in val_s for ch in (".", "e", "E")):
                out[key] = float(val_s)
            else:
                out[key] = int(val_s)
            continue
        except Exception:
            pass

        out[key] = val_s
    return out


def dump_simple_yaml(data: dict) -> str:
    def fmt(v: Any) -> str:
        if v is None:
            return "null"
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, (int, float)):
            return str(v)
        s = str(v)
        if s == "":
            return '""'
        needs_quote = any(ch.isspace() for ch in s) or any(ch in s for ch in (":", "#", '"', "'"))
        if needs_quote:
            s2 = s.replace("\\", "\\\\").replace('"', "\\\"")
            return f'"{s2}"'
        return s

    lines = []
    for k in sorted(data.keys()):
        if not isinstance(k, str):
            continue
        lines.append(f"{k}: {fmt(data[k])}")
    return "\n".join(lines) + "\n"


def load_config(*, apply_env_overrides=None) -> dict:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    cfg = DEFAULT_CONFIG.copy()
    path = get_config_file_for_load()
    if path is not None and path.exists():
        try:
            if path.suffix in (".yaml", ".yml"):
                cfg.update(parse_simple_yaml(path.read_text(encoding="utf-8")))
            else:
                cfg.update(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            pass

    if callable(apply_env_overrides):
        return apply_env_overrides(cfg)
    return cfg


def save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    path = get_config_file_for_save()
    if path.suffix in (".yaml", ".yml"):
        path.write_text(dump_simple_yaml(config), encoding="utf-8")
    else:
        path.write_text(json.dumps(config, indent=2), encoding="utf-8")
