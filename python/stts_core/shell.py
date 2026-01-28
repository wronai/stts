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
        PS1 = f"{self.deps.Colors.GREEN}🔊 stts(py)>{self.deps.Colors.NC} "

        yaml_mode_fn = getattr(self.deps, "_yaml_mode", None)
        yaml_mode = bool(yaml_mode_fn()) if callable(yaml_mode_fn) else False

        if not yaml_mode:
            self.deps.cprint(self.deps.Colors.BOLD + self.deps.Colors.CYAN, "\nSTTS (python) - Voice Shell\n")
            if getattr(self.info, "os_name", None) == "linux":
                try:
                    src, sink = self.deps.get_active_pulse_devices()
                except Exception:
                    src, sink = None, None
                if src or sink:
                    self.deps.cprint(self.deps.Colors.CYAN, "Aktywne urządzenia (PulseAudio):")
                    if src:
                        print(f"  mic: {src}")
                    if sink:
                        print(f"  speaker: {sink}")

            stt_state = "disabled"
            if self.stt:
                stt_state = f"{getattr(self.stt, 'name', 'stt')} model={getattr(self.stt, 'model', '')}"
            else:
                reason = f" reason={self._stt_unavailable_reason}" if self._stt_unavailable_reason else ""
                stt_state = (
                    f"disabled (stt_provider={self.config.get('stt_provider')} stt_model={self.config.get('stt_model')}{reason})"
                )
            print(f"STT: {stt_state}")

            tts_state = "disabled"
            if self.tts:
                tts_state = f"{getattr(self.tts, 'name', 'tts')} voice={getattr(self.tts, 'voice', '')}"
            print(f"TTS: {tts_state}")
            print("Komendy: ENTER=STT, 'exit'=wyjście, 'setup'=konfiguracja, 'audio'=urządzenia, 'meter'=poziomy")

        if self.config.get("startup_tts", True):
            self.speak("Powiedz co chcesz zrobić. Naciśnij enter i mów do mikrofonu.")

        while True:
            try:
                cmd = input(PS1).strip()
                stt_used = False
                if cmd in ["exit", "quit", "q"]:
                    break
                if cmd == "setup":
                    self.config = self.deps.interactive_setup()
                    self.stt = self._init_stt()
                    self.tts = self._init_tts()
                    continue
                if cmd == "audio" and getattr(self.info, "os_name", None) == "linux":
                    self.config["mic_device"] = self.deps.choose_device_interactive(
                        "Wybierz mikrofon (arecord)", self.deps.list_capture_devices_linux()
                    )
                    self.config["speaker_device"] = self.deps.choose_device_interactive(
                        "Wybierz głośnik (info)", self.deps.list_playback_devices_linux()
                    )
                    self.deps.save_config(self.config)
                    continue
                if cmd == "meter" and getattr(self.info, "os_name", None) == "linux":
                    mics = self.deps.list_capture_devices_linux()
                    res = self.deps.mic_meter(mics)
                    self.config["mic_device"] = res.get("selected")
                    self.deps.save_config(self.config)
                    continue

                if cmd.startswith("nlp "):
                    nl = cmd[4:].strip()
                    if not nl:
                        continue
                    translated = self.deps.nlp2cmd_translate(nl)
                    if translated and self.deps.nlp2cmd_confirm(translated):
                        cmd = translated
                    else:
                        continue

                if not cmd:
                    stt_used = True
                    if (
                        self.config.get("mic_device") is None
                        and getattr(self.info, "os_name", None) == "linux"
                        and self.config.get("audio_auto_switch")
                    ):
                        det_fn = getattr(self.deps, "auto_detect_mic", None)
                        if callable(det_fn):
                            det = det_fn(self.deps.list_capture_devices_linux())
                            if det:
                                self.config["mic_device"] = det
                                self.deps.save_config(self.config)

                    try:
                        self.deps.nlp2cmd_prewarm(self.config)
                    except Exception:
                        pass

                    cmd = self.listen()
                    if not cmd:
                        continue
                    translated = self.deps.nlp2cmd_translate(cmd, config=self.config)
                    looks_fn = getattr(self.deps, "_looks_like_natural_language", None)
                    if (not translated) and callable(looks_fn) and looks_fn(cmd):
                        translated = self.deps.nlp2cmd_translate(cmd, config=self.config, force=True)
                    if translated:
                        if self.deps.nlp2cmd_confirm(translated):
                            try:
                                self.deps.emit_stt_event_yaml(cmd, action="execute", translated=translated, reason=None)
                            except Exception:
                                pass
                            cmd = translated
                        else:
                            try:
                                self.deps.emit_stt_event_yaml(
                                    cmd, action="skipped", translated=translated, reason="confirm_declined"
                                )
                            except Exception:
                                pass
                            continue
                    else:
                        allow_raw = os.environ.get("STTS_EXEC_RAW_STT", "0").strip().lower() in (
                            "1",
                            "true",
                            "yes",
                            "y",
                        )
                        if not allow_raw:
                            try:
                                self.deps.emit_stt_event_yaml(cmd, action="skipped", translated=None, reason="no_translation")
                            except Exception:
                                pass
                            continue
                        if callable(looks_fn) and looks_fn(cmd):
                            self.deps.cprint(self.deps.Colors.YELLOW, "⚠️  To wygląda jak tekst naturalny, nie komenda shell.")
                            self.deps.cprint(
                                self.deps.Colors.CYAN,
                                "💡 Włącz tłumaczenie: STTS_NLP2CMD_ENABLED=1 ./stts  (lub wpisz: nlp <tekst>)",
                            )
                            continue

                self.deps.cprint(self.deps.Colors.BLUE, f"▶️  {cmd}")

                is_dangerous, reason = self.deps.is_dangerous_command(cmd)
                if is_dangerous:
                    self.deps.cprint(self.deps.Colors.RED, f"🚫 ZABLOKOWANO: {reason}")
                    continue
                if self.config.get("safe_mode", False):
                    self.deps.cprint(self.deps.Colors.YELLOW, "🔒 SAFE MODE")
                    ans = input("Uruchomić? (y/n): ").strip().lower()
                    if ans != "y":
                        continue

                output, code, printed = self.run_command_any(cmd)
                if output.strip() and not printed:
                    print(output)

                lines = [l.strip() for l in output.splitlines() if l.strip()]
                if lines:
                    last = lines[-1]
                    if last != cmd and len(last) > 3:
                        self.deps.cprint(self.deps.Colors.MAGENTA, f"📢 {last[:80]}")
                        self.speak(last)

                if code != 0:
                    self.deps.cprint(self.deps.Colors.RED, f"❌ Exit code: {code}")
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
        def log(msg: str):
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            line = f"[{ts}] {msg}"
            print(line, file=sys.stderr, flush=True)
            if log_file:
                try:
                    with open(log_file, "a") as f:
                        f.write(line + "\n")
                except Exception:
                    pass

        ww = (wake_word or "hejken").strip() or "hejken"
        try:
            self.config["_daemon"] = True
        except Exception:
            pass
        self.deps.cprint(self.deps.Colors.BOLD + self.deps.Colors.CYAN, f"\n🎙️  STTS Daemon Mode (wake-word: {ww})\n")
        log(f"nlp2cmd service: {nlp2cmd_url}")
        log(f"nlp2cmd timeout: {nlp2cmd_timeout}s")
        log(f"execute commands: {execute}")
        log(f"Say '{ww} <command>' to execute. Ctrl+C to stop.")

        rules = list(triggers or [])
        if rules:
            log(f"triggers loaded: {len(rules)}")

        wake_patterns = None
        if wake_word:
            pat = self.deps._wake_word_phrase_to_pattern(ww)
            if pat:
                wake_patterns = [pat]
                log(f"wake-word: {ww}")

        wake_only_two_stage = False
        try:
            if (self.config.get("stt_provider") == "vosk") and wake_word and len(ww) <= 3:
                wake_only_two_stage = True
                log("wake-word mode: two-stage (vosk grammar)")
        except Exception:
            wake_only_two_stage = False

        prev_grammar = None
        if wake_only_two_stage:
            try:
                prev_grammar = self.config.get("stt_vosk_grammar")
            except Exception:
                prev_grammar = None

        log("🔎 Checking nlp2cmd /health ...")
        if not self.deps.nlp2cmd_service_health(nlp2cmd_url, timeout=2.5):
            log("❌ nlp2cmd service is not healthy / not reachable")
            log("   Start it first, e.g.: nlp2cmd service --host 0.0.0.0 --port 8008")
            if self.tts:
                try:
                    self.speak("Serwis nlp2cmd nie odpowiada")
                except Exception:
                    pass
            return 2

        if self.tts and self.config.get("startup_tts", True):
            self.speak(f"Słucham. Powiedz {ww} i wydaj polecenie.")

        self._suppress_wake_word_logging = True

        while True:
            try:
                log("🎤 Listening...")
                if wake_only_two_stage:
                    try:
                        grammar_words = self.deps.generate_wake_word_variants(ww, max_variants=24)
                        if not grammar_words:
                            grammar_words = [ww]
                        log(f"wake-word grammar variants: {len(grammar_words)}")
                        self.config["stt_vosk_grammar"] = json.dumps(grammar_words, ensure_ascii=False)
                    except Exception:
                        pass

                    text = self.listen()

                    try:
                        if prev_grammar is None:
                            self.config.pop("stt_vosk_grammar", None)
                        else:
                            self.config["stt_vosk_grammar"] = prev_grammar
                    except Exception:
                        pass
                else:
                    text = self.listen()

                if not text:
                    if wake_only_two_stage:
                        log("⏭️  Wake-word stage: no transcript (try speaking louder / closer)")
                    continue

                log(f"📝 Heard: {text}")
                matched, remaining = self.deps.check_wake_word(text, patterns=wake_patterns)
                if not matched:
                    log("⏭️  No wake word, ignoring")
                    continue

                if not remaining:
                    log("🔔 Wake word detected, listening for command...")
                    if self.tts:
                        self.speak("Słucham")
                    remaining = self.listen()
                    if not remaining:
                        log("❌ No command heard")
                        continue
                    remaining = self.deps.normalize_daemon_command(remaining)
                    log(f"📝 Command: {remaining}")
                else:
                    remaining = self.deps.normalize_daemon_command(remaining)
                    log(f"📝 Command: {remaining}")

                if not remaining:
                    log("❌ Empty command after normalization")
                    continue

                trig_cmd = self.deps.match_trigger(remaining, rules)
                if trig_cmd:
                    log(f"⚡ Trigger matched -> {trig_cmd}")
                    ok, reason = self.deps.check_command_safety(trig_cmd, self.config, dry_run=False)
                    if not ok:
                        log(f"🚫 Trigger blocked: {reason}")
                        continue
                    out, code, printed = self.run_command_any(trig_cmd)
                    if out.strip() and not printed:
                        print(out)
                    if code != 0:
                        log(f"❌ Exit code: {code}")
                    continue

                query_text = f"shell: {remaining}"
                log(f"🚀 Sending to nlp2cmd: {query_text}")
                result = self.deps.nlp2cmd_service_query(
                    query=query_text,
                    url=nlp2cmd_url,
                    execute=execute,
                    timeout=float(nlp2cmd_timeout or 30.0),
                )
                if not result:
                    log("❌ nlp2cmd query failed")
                    if self.tts:
                        self.speak("Nie udało się przetworzyć")
                    continue

                if not result.get("success"):
                    errors = result.get("errors") or ["Unknown error"]
                    log(f"❌ nlp2cmd error: {errors}")
                    if self.tts:
                        self.speak(f"Błąd: {errors[0][:50]}")
                    continue

                cmd = result.get("command", "")
                confidence = result.get("confidence", 0)
                log(f"✅ Command: {cmd} (confidence: {confidence:.2f})")

                if self.tts:
                    self.speak(f"Wykonuję: {cmd[:80]}")

                exec_result = result.get("execution_result")
                if exec_result:
                    if exec_result.get("success"):
                        exit_code = exec_result.get("exit_code")
                        duration_ms = exec_result.get("duration_ms")
                        log(f"🏁 Executed by nlp2cmd service (exit_code={exit_code}, duration_ms={duration_ms})")

                        stdout = exec_result.get("stdout", "") or ""
                        stderr = exec_result.get("stderr", "") or ""

                        if stdout:
                            try:
                                print(stdout, end="" if stdout.endswith("\n") else "\n", flush=True)
                            except Exception:
                                pass
                        if stderr:
                            try:
                                print(
                                    stderr,
                                    end="" if stderr.endswith("\n") else "\n",
                                    file=sys.stderr,
                                    flush=True,
                                )
                            except Exception:
                                pass

                        if stdout.strip() and self.tts:
                            lines = [l.strip() for l in stdout.splitlines() if l.strip()]
                            if lines:
                                self.speak(lines[-1][:100])
                    else:
                        exit_code = exec_result.get("exit_code")
                        duration_ms = exec_result.get("duration_ms")
                        stderr = exec_result.get("stderr", "") or ""
                        stdout = exec_result.get("stdout", "") or ""

                        log(f"❌ Execution failed in nlp2cmd service (exit_code={exit_code}, duration_ms={duration_ms})")
                        if stdout:
                            try:
                                print(stdout, end="" if stdout.endswith("\n") else "\n", flush=True)
                            except Exception:
                                pass
                        if stderr:
                            try:
                                print(
                                    stderr,
                                    end="" if stderr.endswith("\n") else "\n",
                                    file=sys.stderr,
                                    flush=True,
                                )
                            except Exception:
                                pass
                        if self.tts:
                            self.speak("Komenda nie powiodła się")
                else:
                    log(f"▶️  Executing locally (nlp2cmd returned only translation): {cmd}")

                    ok, reason = self.deps.check_command_safety(cmd, self.config, dry_run=False)
                    if not ok:
                        log(f"🚫 Blocked (local execute): {reason}")
                        if self.tts:
                            self.speak("Zablokowano komendę")
                        continue

                    out, code, _ = self.run_command_any(cmd)
                    if out.strip():
                        print(out, flush=True)
                        lines = [l.strip() for l in out.splitlines() if l.strip()]
                        if lines and self.tts:
                            self.speak(lines[-1][:100])
                    if code != 0:
                        log(f"❌ Exit code: {code}")

            except KeyboardInterrupt:
                log("🛑 Stopping daemon...")
                break
            except Exception as e:
                log(f"❌ Error: {e}")
                continue

        log("👋 Daemon stopped")
        return 0
