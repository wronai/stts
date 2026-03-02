"""Daemon mode handlers for VoiceShell."""
import datetime
import json
import sys
from typing import Any, List, Optional, Tuple


class DaemonHandlers:
    """Handles daemon mode logic for VoiceShell."""

    def __init__(self, shell: Any):
        self.shell = shell
        self.deps = shell.deps
        self.config = shell.config
        self.log_file: Optional[str] = None
        self.nlp2cmd_url: str = "http://localhost:8000"
        self.nlp2cmd_timeout: float = 30.0
        self.execute: bool = True
        self.triggers: List[Tuple[str, str, bool]] = []
        self.wake_word: str = "hejken"
        self.wake_patterns: Optional[List[str]] = None
        self.wake_only_two_stage: bool = False
        self.prev_grammar: Optional[str] = None

    def init(
        self,
        nlp2cmd_url: str,
        execute: bool,
        nlp2cmd_timeout: float,
        log_file: Optional[str],
        triggers: Optional[List[Tuple[str, str, bool]]],
        wake_word: Optional[str],
    ) -> int:
        """Initialize daemon mode. Returns exit code if should stop, 0 to continue."""
        self.log_file = log_file
        self.nlp2cmd_url = nlp2cmd_url
        self.nlp2cmd_timeout = nlp2cmd_timeout
        self.execute = execute
        self.triggers = list(triggers or [])
        self.wake_word = (wake_word or "hejken").strip() or "hejken"

        # Mark as daemon mode
        try:
            self.config["_daemon"] = True
        except Exception:
            pass

        self.shell._suppress_wake_word_logging = True

        # Print welcome
        self.deps.cprint(
            self.deps.Colors.BOLD + self.deps.Colors.CYAN,
            f"\n🎙️  STTS Daemon Mode (wake-word: {self.wake_word})\n"
        )

        # Log startup info
        self.log(f"nlp2cmd service: {nlp2cmd_url}")
        self.log(f"nlp2cmd timeout: {nlp2cmd_timeout}s")
        self.log(f"execute commands: {execute}")
        self.log(f"Say '{self.wake_word}' and command to execute. Ctrl+C to stop.")

        if self.triggers:
            self.log(f"triggers loaded: {len(self.triggers)}")

        # Setup wake patterns
        if wake_word:
            pat = self.deps._wake_word_phrase_to_pattern(self.wake_word)
            if pat:
                self.wake_patterns = [pat]
                self.log(f"wake-word: {self.wake_word}")

        # Check for two-stage mode (vosk + short wake word)
        try:
            if (self.config.get("stt_provider") == "vosk") and wake_word and len(self.wake_word) <= 3:
                self.wake_only_two_stage = True
                self.log("wake-word mode: two-stage (vosk grammar)")
        except Exception:
            self.wake_only_two_stage = False

        if self.wake_only_two_stage:
            try:
                self.prev_grammar = self.config.get("stt_vosk_grammar")
            except Exception:
                self.prev_grammar = None

        # Health check
        self.log("🔎 Checking nlp2cmd /health ...")
        if not self.deps.nlp2cmd_service_health(nlp2cmd_url, timeout=2.5):
            self.log("❌ nlp2cmd service is not healthy / not reachable")
            self.log("   Start it first, e.g.: nlp2cmd service --host 0.0.0.0 --port 8008")
            if self.shell.tts:
                try:
                    self.shell.speak("Serwis nlp2cmd nie odpowiada")
                except Exception:
                    pass
            return 2

        if self.shell.tts and self.config.get("startup_tts", True):
            self.shell.speak(f"Słucham. Powiedz {self.wake_word} i wydaj polecenie.")

        return 0

    def log(self, msg: str) -> None:
        """Log message to stderr and optionally to file."""
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line, file=sys.stderr, flush=True)
        if self.log_file:
            try:
                with open(self.log_file, "a") as f:
                    f.write(line + "\n")
            except Exception:
                pass

    def listen_with_wake_word(self) -> Optional[str]:
        """Listen for audio, optionally with wake-word grammar."""
        if self.wake_only_two_stage:
            try:
                grammar_words = self.deps.generate_wake_word_variants(self.wake_word, max_variants=24)
                if not grammar_words:
                    grammar_words = [self.wake_word]
                self.log(f"wake-word grammar variants: {len(grammar_words)}")
                self.config["stt_vosk_grammar"] = json.dumps(grammar_words, ensure_ascii=False)
            except Exception:
                pass

            text = self.shell.listen()

            # Restore previous grammar
            try:
                if self.prev_grammar is None:
                    self.config.pop("stt_vosk_grammar", None)
                else:
                    self.config["stt_vosk_grammar"] = self.prev_grammar
            except Exception:
                pass
        else:
            text = self.shell.listen()

        return text

    def process_wake_word(self, text: str) -> Tuple[bool, str]:
        """Process wake word detection. Returns (should_continue, command)."""
        self.log(f"📝 Heard: {text}")
        matched, remaining = self.deps.check_wake_word(text, patterns=self.wake_patterns)

        if not matched:
            self.log("⏭️  No wake word, ignoring")
            return False, ""

        if not remaining:
            self.log("🔔 Wake word detected, listening for command...")
            if self.shell.tts:
                self.shell.speak("Słucham")
            remaining = self.shell.listen()
            if not remaining:
                self.log("❌ No command heard")
                return False, ""
            remaining = self.deps.normalize_daemon_command(remaining)
            self.log(f"📝 Command: {remaining}")
        else:
            remaining = self.deps.normalize_daemon_command(remaining)
            self.log(f"📝 Command: {remaining}")

        if not remaining:
            self.log("❌ Empty command after normalization")
            return False, ""

        return True, remaining

    def check_triggers(self, command: str) -> bool:
        """Check if command matches a trigger. Returns True if handled."""
        trig_cmd = self.deps.match_trigger(command, self.triggers)
        if not trig_cmd:
            return False

        self.log(f"⚡ Trigger matched -> {trig_cmd}")
        ok, reason = self.deps.check_command_safety(trig_cmd, self.config, dry_run=False)
        if not ok:
            self.log(f"🚫 Trigger blocked: {reason}")
            return True

        out, code, printed = self.shell.run_command_any(trig_cmd)
        if out.strip() and not printed:
            print(out)
        if code != 0:
            self.log(f"❌ Exit code: {code}")
        return True

    def query_nlp2cmd(self, command: str) -> Optional[dict]:
        """Query nlp2cmd service. Returns result dict or None on failure."""
        query_text = f"shell: {command}"
        self.log(f"🚀 Sending to nlp2cmd: {query_text}")

        result = self.deps.nlp2cmd_service_query(
            query=query_text,
            url=self.nlp2cmd_url,
            execute=self.execute,
            timeout=float(self.nlp2cmd_timeout or 30.0),
        )

        if not result:
            self.log("❌ nlp2cmd query failed")
            if self.shell.tts:
                self.shell.speak("Nie udało się przetworzyć")
            return None

        if not result.get("success"):
            errors = result.get("errors") or ["Unknown error"]
            self.log(f"❌ nlp2cmd error: {errors}")
            if self.shell.tts:
                self.shell.speak(f"Błąd: {errors[0][:50]}")
            return None

        return result

    def execute_from_result(self, result: dict) -> None:
        """Execute command from nlp2cmd result."""
        cmd = result.get("command", "")
        confidence = result.get("confidence", 0)
        self.log(f"✅ Command: {cmd} (confidence: {confidence:.2f})")

        if self.shell.tts:
            self.shell.speak(f"Wykonuję: {cmd[:80]}")

        exec_result = result.get("execution_result")
        if exec_result:
            self._handle_service_execution(exec_result)
        else:
            self._handle_local_execution(cmd)

    def _handle_service_execution(self, exec_result: dict) -> None:
        """Handle execution that was done by nlp2cmd service."""
        if exec_result.get("success"):
            exit_code = exec_result.get("exit_code")
            duration_ms = exec_result.get("duration_ms")
            self.log(f"🏁 Executed by nlp2cmd service (exit_code={exit_code}, duration_ms={duration_ms})")

            stdout = exec_result.get("stdout", "") or ""
            stderr = exec_result.get("stderr", "") or ""

            if stdout:
                try:
                    print(stdout, end="" if stdout.endswith("\n") else "\n", flush=True)
                except Exception:
                    pass
            if stderr:
                try:
                    print(stderr, end="" if stderr.endswith("\n") else "\n", file=sys.stderr, flush=True)
                except Exception:
                    pass

            if stdout.strip() and self.shell.tts:
                lines = [l.strip() for l in stdout.splitlines() if l.strip()]
                if lines:
                    self.shell.speak(lines[-1][:100])
        else:
            exit_code = exec_result.get("exit_code")
            duration_ms = exec_result.get("duration_ms")
            stderr = exec_result.get("stderr", "") or ""
            stdout = exec_result.get("stdout", "") or ""

            self.log(f"❌ Execution failed in nlp2cmd service (exit_code={exit_code}, duration_ms={duration_ms})")
            if stdout:
                try:
                    print(stdout, end="" if stdout.endswith("\n") else "\n", flush=True)
                except Exception:
                    pass
            if stderr:
                try:
                    print(stderr, end="" if stderr.endswith("\n") else "\n", file=sys.stderr, flush=True)
                except Exception:
                    pass
            if self.shell.tts:
                self.shell.speak("Komenda nie powiodła się")

    def _handle_local_execution(self, cmd: str) -> None:
        """Handle local execution when service only returned translation."""
        self.log(f"▶️  Executing locally (nlp2cmd returned only translation): {cmd}")

        ok, reason = self.deps.check_command_safety(cmd, self.config, dry_run=False)
        if not ok:
            self.log(f"🚫 Blocked (local execute): {reason}")
            if self.shell.tts:
                self.shell.speak("Zablokowano komendę")
            return

        out, code, _ = self.shell.run_command_any(cmd)
        if out.strip():
            print(out, flush=True)
            lines = [l.strip() for l in out.splitlines() if l.strip()]
            if lines and self.shell.tts:
                self.shell.speak(lines[-1][:100])
        if code != 0:
            self.log(f"❌ Exit code: {code}")

    def handle_error(self, e: Exception) -> bool:
        """Handle daemon loop error. Returns True if should stop (KeyboardInterrupt)."""
        if isinstance(e, KeyboardInterrupt):
            self.log("🛑 Stopping daemon...")
            return True
        self.log(f"❌ Error: {e}")
        return False
