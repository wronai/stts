from __future__ import annotations

import os
import signal
import sys
from pathlib import Path


def output_format() -> str:
    return os.environ.get("STTS_OUTPUT_FORMAT", "yaml").strip().lower()


def yaml_mode() -> bool:
    return output_format() in ("yaml", "yml")


def yaml_out():
    return sys.__stdout__ if yaml_mode() else sys.stdout


def text_out():
    return sys.stderr if yaml_mode() else sys.stdout


def stdout_isatty() -> bool:
    try:
        return sys.__stdout__.isatty() if yaml_mode() else sys.stdout.isatty()
    except Exception:
        return False


def load_dotenv() -> None:
    candidates: list[Path] = []
    try:
        here = Path(__file__).resolve().parent
        candidates.append(Path.cwd() / ".env")
        candidates.append(here / ".env")
        candidates.append(here.parent / ".env")
    except Exception:
        pass

    for p in candidates:
        try:
            if not p.exists() or not p.is_file():
                continue
            for line in p.read_text(encoding="utf-8").splitlines():
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                if s.lower().startswith("export "):
                    s = s[7:].strip()
                if "=" not in s:
                    continue
                k, v = s.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if not k:
                    continue
                os.environ.setdefault(k, v)
            break
        except Exception:
            continue


def set_sigpipe_default() -> None:
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except Exception:
        return
