"""Shell utilities for STTS providers."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional


class Colors:
    """ANSI color codes."""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    BLUE = '\033[0;34m'
    MAGENTA = '\033[0;35m'
    CYAN = '\033[0;36m'
    BOLD = '\033[1m'
    NC = '\033[0m'


def cprint(color: str, text: str, end: str = "\n"):
    """Print colored text to stderr."""
    try:
        print(f"{color}{text}{Colors.NC}", end=end, file=os.sys.stderr, flush=True)
    except BrokenPipeError:
        return


@dataclass
class SystemInfo:
    """System information for provider availability checks."""
    os_name: str
    os_version: str
    arch: str
    cpu_cores: int
    ram_gb: float
    gpu_name: Optional[str]
    gpu_vram_gb: Optional[float]
    is_rpi: bool
    has_mic: bool


def detect_system(fast: bool = False) -> SystemInfo:
    """Detect system information."""
    os_name = platform.system().lower()
    os_version = platform.release()
    arch = platform.machine()
    cpu_cores = os.cpu_count() or 1

    ram_gb = 4.0
    try:
        if os_name == "linux":
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        ram_kb = int(line.split()[1])
                        ram_gb = ram_kb / 1024 / 1024
                        break
    except Exception:
        pass

    gpu_name = None
    gpu_vram_gb = None
    if not fast:
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split(", ")
                gpu_name = parts[0]
                gpu_vram_gb = float(parts[1]) / 1024 if len(parts) > 1 else None
        except Exception:
            pass

    is_rpi = False
    try:
        if os_name == "linux" and os.path.exists("/proc/device-tree/model"):
            with open("/proc/device-tree/model") as f:
                model = f.read()
                is_rpi = "raspberry" in model.lower()
    except Exception:
        pass

    has_mic = False
    if not fast:
        try:
            if os_name == "linux":
                result = subprocess.run(["arecord", "-l"], capture_output=True, text=True)
                has_mic = "card" in result.stdout.lower()
            else:
                has_mic = True
        except Exception:
            pass

    return SystemInfo(
        os_name=os_name,
        os_version=os_version,
        arch=arch,
        cpu_cores=cpu_cores,
        ram_gb=round(ram_gb, 1),
        gpu_name=gpu_name,
        gpu_vram_gb=round(gpu_vram_gb, 1) if gpu_vram_gb else None,
        is_rpi=is_rpi,
        has_mic=has_mic,
    )


def play_audio(path: str) -> None:
    """Play audio file using aplay."""
    try:
        subprocess.run(["aplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass
