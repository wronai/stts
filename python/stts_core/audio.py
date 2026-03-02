"""Audio recording and device management for STTS."""
import math
import os
import shutil
import struct
import subprocess
import sys
import time
import wave
from pathlib import Path
from typing import List, Optional, Tuple


def _run_text(argv: List[str], timeout: int = 10) -> str:
    """Run command and return stdout as text."""
    try:
        res = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return res.stdout or ""
    except Exception:
        return ""


def list_capture_devices_linux() -> List[Tuple[str, str]]:
    """List ALSA capture devices on Linux."""
    devices: List[Tuple[str, str]] = []
    out = _run_text(["arecord", "-l"], timeout=3)
    cards = {}
    for line in out.splitlines():
        if line.strip().startswith("card "):
            # card 0: PCH [HDA Intel PCH], device 0: ALC257 Analog [ALC257 Analog]
            parts = line.split(":", 2)
            if len(parts) >= 2:
                card_num = parts[0].replace("card", "").strip()
                rest = parts[1]
                if "[" in rest:
                    card_name = rest.split("[")[1].split("]")[0]
                else:
                    card_name = rest.strip()
                cards[card_num] = card_name
        if "device" in line:
            # Subdevice #0: subdevice #0 (or similar)
            pass

    # Build hw:X,Y devices from cards
    for card_num, card_name in cards.items():
        devices.append((f"hw:{card_num},0", f"{card_name} (hw:{card_num},0)"))

    # Add plughw variants for USB mics
    for card_num, card_name in cards.items():
        devices.insert(0, (f"plughw:{card_num},0", f"{card_name} (plughw)"))

    # Check for additional USB devices in /proc/asound/cards
    try:
        with open("/proc/asound/cards", "r") as f:
            for line in f:
                if "USB" in line:
                    parts = line.split()
                    if parts:
                        try:
                            card_idx = int(parts[0])
                            usb_name = " ".join(parts[2:]) if len(parts) > 2 else "USB Audio"
                            hw_str = f"hw:{card_idx},0"
                            if not any(hw_str in d[0] for d in devices):
                                devices.insert(0, (hw_str, f"{usb_name} (hw:{card_idx},0)"))
                        except ValueError:
                            pass
    except Exception:
        pass

    uniq = []
    seen = set()
    for dev, desc in devices:
        if dev not in seen:
            seen.add(dev)
            uniq.append((dev, desc))

    # Always add default
    if not any(d[0] == "default" for d in uniq):
        uniq.insert(0, ("default", "System default (default)"))

    return uniq


def list_playback_devices_linux() -> List[Tuple[str, str]]:
    """List playback devices using aplay -l."""
    devices: List[Tuple[str, str]] = []
    out = _run_text(["aplay", "-l"], timeout=3)
    cards = {}
    for line in out.splitlines():
        if line.strip().startswith("card "):
            parts = line.split(":", 2)
            if len(parts) >= 2:
                card_num = parts[0].replace("card", "").strip()
                rest = parts[1]
                if "[" in rest:
                    card_name = rest.split("[")[1].split("]")[0]
                else:
                    card_name = rest.strip()
                cards[card_num] = card_name

    for card_num, card_name in cards.items():
        devices.append((f"hw:{card_num},0", f"{card_name} (hw:{card_num},0)"))
        devices.insert(0, (f"plughw:{card_num},0", f"{card_name} (plughw)"))

    uniq = []
    seen = set()
    for dev, desc in devices:
        if dev not in seen:
            seen.add(dev)
            uniq.append((dev, desc))

    if not any(d[0] == "default" for d in uniq):
        uniq.insert(0, ("default", "System default"))

    return uniq


def get_active_pulse_devices() -> Tuple[Optional[str], Optional[str]]:
    """Get active PulseAudio source and sink."""
    if not shutil.which("pactl"):
        return None, None
    src = None
    sink = None
    try:
        out = _run_text(["pactl", "info"], timeout=2)
        for line in out.splitlines():
            if line.startswith("Default Source:"):
                src = line.split(":", 1)[1].strip()
            if line.startswith("Default Sink:"):
                sink = line.split(":", 1)[1].strip()
    except Exception:
        pass
    return src, sink


def analyze_wav(path: str) -> dict:
    """Analyze WAV file and return audio metrics."""
    try:
        with wave.open(path, "rb") as wf:
            channels = wf.getnchannels()
            rate = wf.getframerate()
            width = wf.getsampwidth()
            frames = wf.getnframes()
            raw = wf.readframes(frames)

        if width not in (1, 2, 4) or not raw:
            return {"ok": False, "reason": "unsupported"}

        if width == 1:
            max_int = 127.0
            samples = [(b - 128) for b in raw]
        elif width == 2:
            max_int = 32767.0
            samples = [int.from_bytes(raw[i:i+2], "little", signed=True) for i in range(0, len(raw), 2)]
        else:
            max_int = 2147483647.0
            samples = [int.from_bytes(raw[i:i+4], "little", signed=True) for i in range(0, len(raw), 4)]

        if channels > 1:
            mono = []
            for i in range(0, len(samples), channels):
                chunk = samples[i:i+channels]
                if not chunk:
                    break
                mono.append(sum(chunk) / len(chunk))
            samples_f = mono
        else:
            samples_f = samples

        n = len(samples_f)
        if n == 0:
            return {"ok": False, "reason": "empty"}

        peak = max(abs(float(s)) for s in samples_f)
        mean_sq = sum((float(s) * float(s)) for s in samples_f) / n
        rms = math.sqrt(mean_sq)

        if rms <= 0:
            rms_db = -120.0
        else:
            rms_db = 20.0 * math.log10(rms / max_int)

        if peak <= 0:
            crest_db = 0.0
        else:
            crest_db = 20.0 * math.log10(peak / (rms + 1e-9))

        dur = float(n) / float(rate)

        cls = "speech"
        if rms_db < -55.0:
            cls = "silence"
        elif crest_db < 6.0 and rms_db > -35.0:
            cls = "noise"

        return {
            "ok": True,
            "channels": channels,
            "rate": rate,
            "width": width,
            "duration_s": round(dur, 2),
            "rms_dbfs": round(rms_db, 1),
            "crest_db": round(crest_db, 1),
            "class": cls,
        }
    except Exception:
        return {"ok": False, "reason": "read_error"}


def _arecord_raw(device: Optional[str], seconds: float, rate: int = 16000) -> bytes:
    """Record raw audio using arecord."""
    cmd = ["arecord"]
    if device:
        cmd += ["-D", device]
    cmd += [
        "-q",
        "-d", str(max(1, int(math.ceil(seconds)))),
        "-r", str(rate),
        "-c", "1",
        "-f", "S16_LE",
        "-t", "raw",
        "-",
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, timeout=max(2, int(seconds) + 2))
        return res.stdout or b""
    except Exception:
        return b""


def _rms_dbfs_s16le(raw: bytes) -> float:
    """Calculate RMS dBFS from S16LE raw audio."""
    if not raw:
        return -120.0
    n = len(raw) // 2
    if n <= 0:
        return -120.0
    try:
        samples = struct.unpack("<" + "h" * n, raw[: n * 2])
    except Exception:
        return -120.0
    mean_sq = sum((float(s) * float(s)) for s in samples) / float(n)
    rms = math.sqrt(mean_sq)
    if rms <= 0:
        return -120.0
    return 20.0 * math.log10(rms / 32767.0)


def record_audio_vad(
    max_duration: float = 5.0,
    output_path: str = "/tmp/stts_audio.wav",
    device: Optional[str] = None,
    silence_ms: int = 800,
    threshold_db: float = -45.0,
    rate: int = 16000,
    cprint=None,
    Colors=None,
) -> str:
    """Record with VAD: stop early after silence_ms of silence below threshold_db."""
    t0 = time.perf_counter()
    ts = time.strftime("%H:%M:%S")

    if cprint and Colors:
        cprint(Colors.GREEN, f"[{ts}] 🎤 Mów (max {max_duration:.0f}s, VAD)...", end=" ")

    cmd = ["arecord"]
    if device:
        cmd += ["-D", device]
    cmd += ["-q", "-r", str(rate), "-c", "1", "-f", "S16_LE", "-t", "raw", "-"]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except Exception as e:
        if cprint and Colors:
            cprint(Colors.RED, f"❌ arecord error: {e}")
        return ""

    chunk_samples = int(rate * 0.1)  # 100ms chunks
    chunk_bytes = chunk_samples * 2
    silence_samples_needed = int(silence_ms / 100)
    max_samples = int(max_duration * 10)

    all_audio = bytearray()
    silence_count = 0
    speech_detected = False
    sample_count = 0

    try:
        while sample_count < max_samples:
            chunk = proc.stdout.read(chunk_bytes)
            if not chunk:
                break
            all_audio.extend(chunk)
            sample_count += 1

            n = len(chunk) // 2
            if n > 0:
                samples = struct.unpack("<" + "h" * n, chunk[:n * 2])
                mean_sq = sum(float(s) * float(s) for s in samples) / float(n)
                rms = math.sqrt(mean_sq)
                db = 20.0 * math.log10(rms / 32767.0) if rms > 0 else -120.0

                if db > threshold_db:
                    speech_detected = True
                    silence_count = 0
                else:
                    silence_count += 1

                if speech_detected and silence_count >= silence_samples_needed:
                    break
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=1)
        except Exception:
            proc.kill()

    elapsed = time.perf_counter() - t0

    if not all_audio:
        if cprint and Colors:
            cprint(Colors.RED, "❌ Brak danych audio")
        return ""

    try:
        with wave.open(output_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(rate)
            wf.writeframes(bytes(all_audio))
    except Exception as e:
        if cprint and Colors:
            cprint(Colors.RED, f"❌ WAV write error: {e}")
        return ""

    actual_dur = len(all_audio) / 2 / rate
    if speech_detected:
        if cprint and Colors:
            cprint(Colors.GREEN, f"✅ VAD stop ({actual_dur:.1f}s / {elapsed:.1f}s)")
    else:
        print(f"⏱️ ({actual_dur:.1f}s)")

    return output_path


def record_audio(
    duration: int = 2,
    output_path: str = "/tmp/stts_audio.wav",
    device: Optional[str] = None,
    cprint=None,
    Colors=None,
) -> str:
    """Fixed-duration recording (legacy, use record_audio_vad for better UX)."""
    t0 = time.perf_counter()
    ts = time.strftime("%H:%M:%S")

    if cprint and Colors:
        cprint(Colors.GREEN, f"[{ts}] 🎤 Mów ({duration}s)...", end=" ")

    try:
        cmd = ["arecord"]
        if device:
            cmd += ["-D", device]
        cmd += [
            "-d", str(duration),
            "-r", "16000",
            "-c", "1",
            "-f", "S16_LE",
            "-t", "wav",
            output_path,
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=duration + 2)
        elapsed = time.perf_counter() - t0
        if cprint and Colors:
            cprint(Colors.GREEN, f"✅ ({elapsed:.1f}s)")
        return output_path
    except Exception as e:
        if cprint and Colors:
            cprint(Colors.RED, f"❌ Recording failed: {e}")
        return ""


def choose_device_interactive(title: str, devices: List[Tuple[str, str]], cprint=None, Colors=None) -> Optional[str]:
    """Interactive device selection."""
    if cprint and Colors:
        cprint(Colors.CYAN, f"\n{title}")
    print("  0. auto")
    for i, (dev, desc) in enumerate(devices, 1):
        print(f"  {i}. {dev}  {desc}")
    while True:
        sel = input("Wybór (0=auto): ").strip()
        if sel == "" or sel == "0":
            return None
        try:
            idx = int(sel)
            if 1 <= idx <= len(devices):
                return devices[idx - 1][0]
        except ValueError:
            for dev, _ in devices:
                if sel == dev:
                    return dev
        if cprint and Colors:
            cprint(Colors.RED, "❌ Nieprawidłowy wybór")
        else:
            print("❌ Nieprawidłowy wybór")


def mic_meter(
    devices: List[Tuple[str, str]],
    seconds: float = 0.8,
    loops: int = 0,
    cprint=None,
    Colors=None,
) -> dict:
    """Interactive microphone level meter."""
    scores: dict = {d: -120.0 for d, _ in devices}
    i = 0
    while True:
        i += 1
        print("\033[2J\033[H", end="")
        if cprint and Colors:
            cprint(Colors.CYAN, "Mów do mikrofonu teraz (meter). Ctrl+C = stop")
        for idx, (dev, desc) in enumerate(devices, 1):
            raw = _arecord_raw(dev if dev not in ("auto", "0") else None, seconds)
            db = _rms_dbfs_s16le(raw)
            scores[dev] = db
            bar_len = max(0, min(30, int((db + 60) * 0.8)))
            bar = "#" * bar_len
            print(f"{idx:2d}. {dev:10s} {db:6.1f} dBFS  {bar}  {desc}")
        print("\nWybierz numer mikrofonu (0=auto), ENTER=odśwież: ", end="", flush=True)
        try:
            sel = input().strip()
        except KeyboardInterrupt:
            print()
            return {"selected": None, "scores": scores}
        if sel == "":
            if loops and i >= loops:
                return {"selected": None, "scores": scores}
            continue
        if sel in ("0", "auto"):
            return {"selected": None, "scores": scores}
        try:
            nsel = int(sel)
            if 1 <= nsel <= len(devices):
                return {"selected": devices[nsel - 1][0], "scores": scores}
        except ValueError:
            pass


def auto_detect_mic(
    devices: List[Tuple[str, str]],
    seconds: float = 0.8,
    rounds: int = 2,
    cprint=None,
    Colors=None,
) -> Optional[str]:
    """Auto-detect best microphone by signal level."""
    if cprint and Colors:
        cprint(Colors.CYAN, "Mów teraz normalnie do mikrofonu (auto-detekcja)...")
    best_dev = None
    best_db = -120.0
    for _ in range(rounds):
        for dev, _ in devices:
            raw = _arecord_raw(dev if dev not in ("auto", "0") else None, seconds)
            db = _rms_dbfs_s16le(raw)
            if db > best_db:
                best_db = db
                best_dev = dev
    if best_dev and best_db > -55.0:
        if cprint and Colors:
            cprint(Colors.GREEN, f"✅ Wykryto mikrofon: {best_dev} (rms ~ {best_db:.1f} dBFS)")
        return best_dev
    if cprint and Colors:
        cprint(Colors.YELLOW, "⚠️  Nie wykryto sensownego sygnału (cisza). Uruchom 'meter' aby wybrać ręcznie.")
    return None
