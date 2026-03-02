from __future__ import annotations

import atexit
import datetime
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .command_handlers import InteractiveCommandHandlers
from .daemon_handlers import DaemonHandlers


class VoiceShell:
    def __init__(self, config: dict, deps: Any):
        self.deps = deps
        self.config = config
        self.info = deps.detect_system(fast=bool(self.config.get("fast_start", True)))
        self._stt_unavailable_reason = None
        self._warned_stt_disabled = False
        self.stt = self._init_stt()
        self.tts = self._init_tts()
        self._suppress_wake_word_logging = False

        deps.HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        if deps.HISTORY_FILE.exists():
            deps.readline.read_history_file(str(deps.HISTORY_FILE))

        def _write_history():
            try:
                deps.HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
                deps.readline.write_history_file(str(deps.HISTORY_FILE))
            except Exception:
                pass

        atexit.register(_write_history)

    def _init_stt(self):
        provider = self.config.get("stt_provider")
        providers = getattr(self.deps, "STT_PROVIDERS", {})
        if provider in providers:
            cls = providers[provider]
            available, reason = cls.is_available(self.info)
            if available:
                self._stt_unavailable_reason = None
                return cls(
                    model=self.config.get("stt_model"),
                    language=self.config.get("language", "pl"),
                    config=self.config,
                    info=self.info,
                )

            if provider == "vosk":
                do_install = bool(self.config.get("vosk_auto_install", True))
                do_download = bool(self.config.get("vosk_auto_download", True))

                reason_s = str(reason or "")
                if do_install and ("pip install vosk" in reason_s):
                    self.deps.cprint(self.deps.Colors.YELLOW, "📦 Installing vosk (pip)...")
                    try:
                        cls.install(self.info)
                    except Exception:
                        pass

                available2, reason2 = cls.is_available(self.info)
                reason2_s = str(reason2 or "")

                if do_download and ("no models" in reason2_s):
                    model = (self.config.get("stt_model") or "").strip() or (
                        cls.get_recommended_model(self.info) or "small-pl"
                    )
                    self.deps.cprint(self.deps.Colors.YELLOW, f"📥 Downloading Vosk model: {model}")
                    try:
                        cls.download_model(model)
                    except Exception:
                        pass
                    available2, reason2 = cls.is_available(self.info)

                if available2:
                    self._stt_unavailable_reason = None
                    return cls(
                        model=self.config.get("stt_model"),
                        language=self.config.get("language", "pl"),
                        config=self.config,
                        info=self.info,
                    )
                reason = reason2

            self._stt_unavailable_reason = str(reason)
            print(
                f"[stts] ⚠️  STT provider '{provider}' unavailable ({reason}); STT disabled",
                file=sys.stderr,
            )
        return None

    def _init_tts(self):
        provider = self.config.get("tts_provider")
        voice = self.config.get("tts_voice", "pl")
        providers = getattr(self.deps, "TTS_PROVIDERS", {})

        if provider in providers:
            cls = providers[provider]
            inst = cls(voice=voice, config=self.config, info=self.info)
            available, reason = cls.is_available(self.info)
            if available:
                return inst
            if provider == "piper" and self.config.get("piper_auto_install", True):
                return inst

            print(
                f"[stts] ⚠️  TTS provider '{provider}' unavailable ({reason}); TTS disabled",
                file=sys.stderr,
            )
            return None

        if shutil.which("espeak") or shutil.which("espeak-ng"):
            espeak_cls = getattr(self.deps, "EspeakTTS", None)
            if espeak_cls is not None:
                return espeak_cls(voice=voice, config=self.config, info=self.info)
        return None

    def speak(self, text: str):
        if self.tts and self.config.get("auto_tts", True):
            threading.Thread(target=self.tts.speak, args=(text[:200],), daemon=True).start()

    def transcribe(self, audio_path: str) -> str:
        if os.environ.get("STTS_MOCK_STT") == "1":
            sidecar = Path(audio_path).with_suffix(Path(audio_path).suffix + ".txt")
            if sidecar.exists():
                try:
                    return sidecar.read_text(encoding="utf-8").strip()
                except Exception:
                    return ""

        if not self.stt:
            if (not self._warned_stt_disabled) and self.config.get("stt_provider"):
                self._warned_stt_disabled = True
                reason = self._stt_unavailable_reason
                if reason:
                    self.deps.cprint(
                        self.deps.Colors.RED,
                        f"❌ STT disabled: {self.config.get('stt_provider')} ({reason})",
                    )
                else:
                    self.deps.cprint(
                        self.deps.Colors.RED,
                        f"❌ STT disabled: {self.config.get('stt_provider')}",
                    )
            return ""

        t0 = time.perf_counter()

        ts_fn = getattr(self.deps, "_ts", None)
        ts = ts_fn() if callable(ts_fn) else time.strftime("%H:%M:%S")

        self.deps.cprint(self.deps.Colors.YELLOW, f"[{ts}] 🔄 Rozpoznawanie...", end=" ")
        text = self.stt.transcribe(audio_path)
        elapsed = time.perf_counter() - t0
        if text:
            shown = text
            if self._suppress_wake_word_logging and hasattr(self.deps, "check_wake_word"):
                pats = self.config.get("daemon_wake_patterns") if isinstance(self.config, dict) else None
                if not isinstance(pats, list):
                    pats = None
                matched, remaining = self.deps.check_wake_word(text, patterns=pats)
                if matched and remaining:
                    shown = remaining
            self.deps.cprint(self.deps.Colors.GREEN, f"✅ \"{shown}\" ({elapsed:.1f}s)")
        else:
            self.deps.cprint(self.deps.Colors.RED, f"❌ Nie rozpoznano ({elapsed:.1f}s)")
        return text

    def listen(self, stt_file: Optional[str] = None) -> str:
        mic = self.config.get("mic_device")
        if stt_file:
            audio_path = stt_file
        elif self.config.get("vad_enabled", True) and getattr(self.info, "os_name", None) == "linux":
            audio_path = self.deps.record_audio_vad(
                max_duration=float(self.config.get("timeout", 5)),
                device=mic,
                silence_ms=self.config.get("vad_silence_ms", 800),
                threshold_db=self.config.get("vad_threshold_db", -45.0),
            )
        else:
            audio_path = self.deps.record_audio(self.config.get("timeout", 2), device=mic)

        if not audio_path:
            return ""

        diag = self.deps.analyze_wav(audio_path)
        if diag.get("ok") and diag.get("class") in ("silence", "noise") and stt_file is None:
            if self.config.get("audio_auto_switch") and getattr(self.info, "os_name", None) == "linux":
                self.deps.cprint(self.deps.Colors.YELLOW, "🔁 Próba auto-wyboru mikrofonu...")
                candidates = self.deps.list_capture_devices_linux()
                best = None
                best_score = -1e9
                for dev, _ in candidates[:6]:
                    if mic and dev == mic:
                        continue
                    tmp = "/tmp/stts_probe.wav"
                    p = self.deps.record_audio(2, output_path=tmp, device=dev)
                    if not p:
                        continue
                    d = self.deps.analyze_wav(p)
                    if not d.get("ok"):
                        continue
                    score = float(d.get("rms_dbfs", -120)) + float(d.get("crest_db", 0))
                    if d.get("class") != "silence" and score > best_score:
                        best = dev
                        best_score = score
                if best:
                    self.deps.cprint(self.deps.Colors.GREEN, f"✅ Wybrano mikrofon: {best}")
                    self.config["mic_device"] = best
                    self.deps.save_config(self.config)
                    audio_path = self.deps.record_audio(self.config.get("timeout", 5), device=best)
                    if not audio_path:
                        return ""

        return self.transcribe(audio_path)

    def run_command(self, cmd: str):
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            return result.stdout + result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "⏰ Timeout (60s)", 124
        except Exception as e:
            return f"❌ Error: {e}", 1

    def run_command_streaming(self, cmd: str):
        """Strumieniowe wykonanie komendy z wypisywaniem linia po linii."""
        try:
            if isinstance(cmd, list):
                argv = cmd
            else:
                if os.name != "nt":
                    argv = ["/bin/bash", "-c", cmd]
                else:
                    argv = ["cmd", "/c", cmd]

            process = subprocess.Popen(
                argv,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )
            output_parts = []
            for line in iter(process.stdout.readline, ""):
                if line:
                    print(line, end="", flush=True)
                    output_parts.append(line)
            process.stdout.close()
            return_code = process.wait()
            return "".join(output_parts), return_code
        except Exception as e:
            return f"❌ Error: {e}", 1

    def run_command_any(self, cmd: str):
        # If pexpect exists, support interactive prompts with TTS + voice reply.
        def _has_pexpect():
            try:
                import pexpect  # noqa: F401

                return True
            except ImportError:
                return False

        if sys.stdin.isatty() and _has_pexpect():
            try:
                return self.run_command_interactive(cmd)
            except Exception:
                pass

        # W pipe (nie-TTY) użyj strumieniowania
        if not sys.stdin.isatty():
            out, code = self.run_command_streaming(cmd)
            return out, code, True
        if self.config.get("stream_cmd", False):
            out, code = self.run_command_streaming(cmd)
            return out, code, True
        out, code = self.run_command(cmd)
        return out, code, False

    def run_command_interactive(self, cmd: str):
        import pexpect

        if os.name != "nt":
            child = pexpect.spawn("/bin/bash", ["-c", cmd], encoding="utf-8", timeout=1)
        else:
            child = pexpect.spawn(cmd, encoding="utf-8", timeout=1)
        output_parts: List[str] = []
        last_nonempty = ""
        printed = False

        def _flush(text: str):
            nonlocal last_nonempty, printed
            if text:
                printed = True
                print(text, end="", flush=True)
                output_parts.append(text)
                for line in text.splitlines():
                    s = line.strip()
                    if s:
                        last_nonempty = s

        while True:
            try:
                idx = child.expect(["\n", pexpect.EOF, pexpect.TIMEOUT])
                if idx == 0:
                    _flush(child.before + "\n")
                elif idx == 1:
                    _flush(child.before)
                    break
                else:
                    # No output for a moment -> likely waiting for input
                    pending = (child.before or "").strip()
                    prompt_text = pending or last_nonempty
                    if prompt_text:
                        self.deps.cprint(self.deps.Colors.MAGENTA, f"📢 {prompt_text[:120]}")
                        self.speak(prompt_text)

                    reply = ""
                    if self.config.get("prompt_voice_first", True):
                        reply = self.listen()
                        reply = (reply or "").strip().lower()
                        if any(
                            x in (prompt_text or "").lower() for x in ("y/n", "[y/n]", "(y/n)", "yes/no")
                        ):
                            if reply in ("tak", "t", "yes", "y", "ok"):
                                reply = "y"
                            elif reply in ("nie", "n", "no"):
                                reply = "n"
                    if not reply:
                        reply = input("⌨️  Odpowiedź: ")
                    child.sendline(reply)
            except pexpect.exceptions.EOF:
                break

        try:
            child.close()
        except Exception:
            pass

        code = child.exitstatus if child.exitstatus is not None else (child.status or 0)
        return "".join(output_parts), code, printed

    def run(self):
        """Interactive voice shell REPL."""
        PS1 = f"{self.deps.Colors.GREEN}🔊 stts(py)>{self.deps.Colors.NC} "
        handlers = InteractiveCommandHandlers(self)
        handlers.print_welcome()

        while True:
            try:
                cmd = input(PS1).strip()

                # Handle built-in commands
                if handlers.handle_exit(cmd):
                    break
                if cmd == "setup":
                    handlers.handle_setup()
                    continue
                if cmd == "audio":
                    if handlers.handle_audio():
                        continue
                if cmd == "meter":
                    if handlers.handle_meter():
                        continue

                # Handle NLP translation
                nlp_result = handlers.handle_nlp(cmd)
                if nlp_result is not None:
                    cmd = nlp_result
                elif not cmd:
                    # Handle voice input
                    cmd = handlers.handle_stt_input()
                    if cmd is None:
                        continue

                # Execute command
                output, code, printed = handlers.execute_command(cmd)
                handlers.handle_output(output, code, printed, cmd)

            except KeyboardInterrupt:
                print()
                continue
            except EOFError:
                break

    def run_daemon(
        self,
        nlp2cmd_url: str = "http://localhost:8000",
        execute: bool = True,
        nlp2cmd_timeout: float = 30.0,
        log_file: Optional[str] = None,
        triggers: Optional[List[Tuple[str, str, bool]]] = None,
        wake_word: Optional[str] = None,
    ) -> int:
        """Daemon mode with wake-word detection and nlp2cmd integration."""
        handlers = DaemonHandlers(self)

        # Initialize daemon
        init_code = handlers.init(
            nlp2cmd_url=nlp2cmd_url,
            execute=execute,
            nlp2cmd_timeout=nlp2cmd_timeout,
            log_file=log_file,
            triggers=triggers,
            wake_word=wake_word,
        )
        if init_code != 0:
            return init_code

        # Main daemon loop
        while True:
            try:
                handlers.log("🎤 Listening...")
                text = handlers.listen_with_wake_word()

                if not text:
                    if handlers.wake_only_two_stage:
                        handlers.log("⏭️  Wake-word stage: no transcript (try speaking louder / closer)")
                    continue

                # Process wake word and get command
                should_continue, command = handlers.process_wake_word(text)
                if not should_continue:
                    continue

                # Check triggers first
                if handlers.check_triggers(command):
                    continue

                # Query nlp2cmd service
                result = handlers.query_nlp2cmd(command)
                if result is None:
                    continue

                # Execute result
                handlers.execute_from_result(result)

            except Exception as e:
                if handlers.handle_error(e):
                    break
                continue

        handlers.log("👋 Daemon stopped")
        return 0
