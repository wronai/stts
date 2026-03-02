"""Command handlers for VoiceShell interactive mode."""
from typing import Any, Optional, Tuple


class InteractiveCommandHandlers:
    """Handles built-in commands for VoiceShell interactive mode."""

    def __init__(self, shell: Any):
        self.shell = shell
        self.deps = shell.deps
        self.config = shell.config
        self.info = shell.info

    def handle_exit(self, cmd: str) -> bool:
        """Handle exit/quit commands. Returns True if should exit."""
        return cmd in ("exit", "quit", "q")

    def handle_setup(self) -> bool:
        """Handle setup command. Returns True if handled."""
        self.config = self.deps.interactive_setup()
        self.shell.config = self.config
        self.shell.stt = self.shell._init_stt()
        self.shell.tts = self.shell._init_tts()
        return True

    def handle_audio(self) -> bool:
        """Handle audio device selection. Returns True if handled."""
        if getattr(self.info, "os_name", None) != "linux":
            return False
        self.config["mic_device"] = self.deps.choose_device_interactive(
            "Wybierz mikrofon (arecord)", self.deps.list_capture_devices_linux()
        )
        self.config["speaker_device"] = self.deps.choose_device_interactive(
            "Wybierz głośnik (info)", self.deps.list_playback_devices_linux()
        )
        self.deps.save_config(self.config)
        return True

    def handle_meter(self) -> bool:
        """Handle mic meter command. Returns True if handled."""
        if getattr(self.info, "os_name", None) != "linux":
            return False
        mics = self.deps.list_capture_devices_linux()
        res = self.deps.mic_meter(mics)
        self.config["mic_device"] = res.get("selected")
        self.deps.save_config(self.config)
        return True

    def handle_nlp(self, cmd: str) -> Optional[str]:
        """Handle nlp translation command. Returns translated command or None."""
        if not cmd.startswith("nlp "):
            return None
        nl = cmd[4:].strip()
        if not nl:
            return None
        translated = self.deps.nlp2cmd_translate(nl)
        if translated and self.deps.nlp2cmd_confirm(translated):
            return translated
        return None

    def handle_stt_input(self) -> Optional[str]:
        """Handle voice input (STT). Returns recognized/translated command or None."""
        # Auto-detect mic if needed
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

        # Prewarm nlp2cmd
        try:
            self.deps.nlp2cmd_prewarm(self.config)
        except Exception:
            pass

        cmd = self.shell.listen()
        if not cmd:
            return None

        # Try translation
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
                return translated
            else:
                try:
                    self.deps.emit_stt_event_yaml(
                        cmd, action="skipped", translated=translated, reason="confirm_declined"
                    )
                except Exception:
                    pass
                return None
        else:
            # No translation - check if we should allow raw STT
            allow_raw = __import__("os").environ.get("STTS_EXEC_RAW_STT", "0").strip().lower() in (
                "1", "true", "yes", "y"
            )
            if not allow_raw:
                try:
                    self.deps.emit_stt_event_yaml(cmd, action="skipped", translated=None, reason="no_translation")
                except Exception:
                    pass
                return None
            if callable(looks_fn) and looks_fn(cmd):
                self.deps.cprint(self.deps.Colors.YELLOW, "⚠️  To wygląda jak tekst naturalny, nie komenda shell.")
                self.deps.cprint(
                    self.deps.Colors.CYAN,
                    "💡 Włącz tłumaczenie: STTS_NLP2CMD_ENABLED=1 ./stts  (lub wpisz: nlp <tekst>)",
                )
                return None
            return cmd

    def execute_command(self, cmd: str) -> Tuple[str, int, bool]:
        """Execute command with safety checks. Returns (output, code, printed)."""
        self.deps.cprint(self.deps.Colors.BLUE, f"▶️  {cmd}")

        # Safety check
        is_dangerous, reason = self.deps.is_dangerous_command(cmd)
        if is_dangerous:
            self.deps.cprint(self.deps.Colors.RED, f"🚫 ZABLOKOWANO: {reason}")
            return "", 1, False

        if self.config.get("safe_mode", False):
            self.deps.cprint(self.deps.Colors.YELLOW, "🔒 SAFE MODE")
            ans = __import__("builtins").input("Uruchomić? (y/n): ").strip().lower()
            if ans != "y":
                return "", 0, False

        return self.shell.run_command_any(cmd)

    def print_welcome(self) -> None:
        """Print welcome message and status."""
        yaml_mode_fn = getattr(self.deps, "_yaml_mode", None)
        yaml_mode = bool(yaml_mode_fn()) if callable(yaml_mode_fn) else False

        if yaml_mode:
            return

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
        if self.shell.stt:
            stt_state = f"{getattr(self.shell.stt, 'name', 'stt')} model={getattr(self.shell.stt, 'model', '')}"
        else:
            reason = f" reason={self.shell._stt_unavailable_reason}" if self.shell._stt_unavailable_reason else ""
            stt_state = (
                f"disabled (stt_provider={self.config.get('stt_provider')} stt_model={self.config.get('stt_model')}{reason})"
            )
        print(f"STT: {stt_state}")

        tts_state = "disabled"
        if self.shell.tts:
            tts_state = f"{getattr(self.shell.tts, 'name', 'tts')} voice={getattr(self.shell.tts, 'voice', '')}"
        print(f"TTS: {tts_state}")
        print("Komendy: ENTER=STT, 'exit'=wyjście, 'setup'=konfiguracja, 'audio'=urządzenia, 'meter'=poziomy")

        if self.config.get("startup_tts", True):
            self.shell.speak("Powiedz co chcesz zrobić. Naciśnij enter i mów do mikrofonu.")

    def handle_output(self, output: str, code: int, printed: bool, cmd: str) -> None:
        """Handle command output and TTS feedback."""
        if output.strip() and not printed:
            print(output)

        lines = [l.strip() for l in output.splitlines() if l.strip()]
        if lines:
            last = lines[-1]
            if last != cmd and len(last) > 3:
                self.deps.cprint(self.deps.Colors.MAGENTA, f"📢 {last[:80]}")
                self.shell.speak(last)

        if code != 0:
            self.deps.cprint(self.deps.Colors.RED, f"❌ Exit code: {code}")
