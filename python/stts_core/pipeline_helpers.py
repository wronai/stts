import contextlib
import os
import sys
from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class PipelineDeps:
    cprint: Callable[..., Any]
    Colors: Any
    check_command_safety: Callable[..., Any]
    argv_to_cmd: Callable[..., str]
    nlp2cmd_prewarm: Callable[..., Any]
    nlp2cmd_prewarm_force: Callable[..., Any]
    nlp2cmd_translate: Callable[..., Any]
    nlp2cmd_confirm: Callable[..., Any]


def run_stt_stream_shell(deps: PipelineDeps, shell, config, stt_file, stream_shell_cmd, dry_run):
    if not stream_shell_cmd:
        deps.cprint(deps.Colors.RED, "❌ Brak --cmd w trybie --stt-stream-shell")
        return 2

    PS1 = f"{deps.Colors.GREEN}🔴 captions>{deps.Colors.NC} "
    print(
        "Voice shell (placeholder): mów do mikrofonu, STT wstawiane w {STT}/{STT_STREAM}. CTRL+C = pomiń, CTRL+D = wyjście",
        file=sys.stderr,
    )

    one_shot = bool(stt_file)
    while True:
        try:
            if sys.stdin.isatty() and (not one_shot):
                _ = input(PS1)

            with contextlib.redirect_stdout(sys.stderr):
                text = shell.listen(stt_file=stt_file) if stt_file else shell.listen()

            if not text:
                if one_shot:
                    return 1
                continue

            t = (text or "").strip()
            if t.lower() in ("exit", "quit", "q"):
                return 0

            print(f"📝 {t}", file=sys.stderr)

            cmd = (stream_shell_cmd or "").replace("{STT}", t).replace("{STT_STREAM}", t)

            if dry_run:
                print(cmd)
                if one_shot:
                    return 0
                continue

            ok, reason = deps.check_command_safety(cmd, config, dry_run)
            if not ok:
                if one_shot:
                    return 0 if reason == "dry-run" else 1
                continue

            out, code, printed = shell.run_command_any(cmd)
            if out.strip() and not printed:
                print(out, end="", flush=True)
            lines = [l.strip() for l in out.splitlines() if l.strip()]
            if lines and shell.tts and config.get("auto_tts", True):
                shell.tts.speak(lines[-1][:200])

            if one_shot:
                return code
        except KeyboardInterrupt:
            print("", file=sys.stderr)
            if one_shot:
                return 130
            continue
        except EOFError:
            return 0


def run_stt_once(deps: PipelineDeps, shell, stt_file):
    with contextlib.redirect_stdout(sys.stderr):
        text = shell.listen(stt_file=stt_file) if stt_file else shell.listen()
    if text:
        print(text)
        return 0 if text else 1
    return 1


def run_nlp2cmd_parallel_fastpath(deps: PipelineDeps, config, shell, stt_file, stt_only, dry_run, rest):
    bin_name = os.environ.get("STTS_NLP2CMD_BIN", "nlp2cmd")
    if not (rest and rest[0] == bin_name and any("{STT}" in a for a in rest)):
        return None

    auto_confirm = ("--auto-confirm" in rest)

    deps.nlp2cmd_prewarm(config)
    if stt_file:
        text = shell.listen(stt_file=stt_file)
        if stt_only:
            print(text)
            return 0 if text else 1
    else:
        with contextlib.redirect_stdout(sys.stderr):
            text = shell.listen()
    if not text:
        return 1

    translated = deps.nlp2cmd_translate(text, config=config, force=True)
    if not translated:
        deps.cprint(deps.Colors.RED, "❌ nlp2cmd: brak wygenerowanej komendy")
        return 1

    if dry_run:
        print(translated)
        return 0

    if not auto_confirm:
        if not deps.nlp2cmd_confirm(translated):
            return 0

    ok, reason = deps.check_command_safety(translated, config, dry_run)
    if not ok:
        return 0 if reason == "dry-run" else 1
    out, code, printed = shell.run_command_any(translated)
    if out.strip() and not printed:
        print(out, end="", flush=True)
    return code


def run_stt_file_placeholder_mode(deps: PipelineDeps, config, shell, stt_file, dry_run, rest):
    deps.nlp2cmd_prewarm(config)
    text = shell.listen(stt_file=stt_file)
    if not text:
        return 1

    expanded = [str(a).replace("{STT}", text).replace("{STT_STREAM}", text) for a in rest]
    cmd = deps.argv_to_cmd(expanded)

    if dry_run:
        print(cmd)
        return 0

    ok, reason = deps.check_command_safety(cmd, config, dry_run)
    if not ok:
        return 0 if reason == "dry-run" else 1

    out, code, printed = shell.run_command_any(cmd)
    if out.strip() and not printed:
        print(out, end="", flush=True)
    lines = [l.strip() for l in out.splitlines() if l.strip()]
    if lines and shell.tts and config.get("auto_tts", True):
        shell.tts.speak(lines[-1][:200])
    return code


def run_stt_file_default_mode(deps: PipelineDeps, config, shell, stt_file, stt_only, dry_run):
    deps.nlp2cmd_prewarm(config)
    text = shell.listen(stt_file=stt_file)
    if stt_only:
        print(text)
        return 0 if text else 1
    if text:
        if dry_run:
            print(text)
            return 0
        translated = deps.nlp2cmd_translate(text, config=config)
        if translated and deps.nlp2cmd_confirm(translated):
            text = translated
        out, code, printed = shell.run_command_any(text)
        if out.strip() and not printed:
            print(out, end="", flush=True)
        return code
    return 1


def run_pipe_dry_run() -> int:
    data = ""
    try:
        data = sys.stdin.read()
    except Exception:
        data = ""
    lines = [l.strip() for l in (data or "").splitlines() if l.strip()]
    cmd = lines[-1] if lines else ""
    if not cmd:
        return 1
    try:
        print(cmd)
    except BrokenPipeError:
        return 0
    return 0


def run_nlp2cmd_stdin_mode(deps: PipelineDeps, config, shell, rest, dry_run):
    bin_name = os.environ.get("STTS_NLP2CMD_BIN", "nlp2cmd")
    if not (
        rest
        and rest[0] == bin_name
        and (not sys.stdin.isatty())
        and any(a in ("stdin", "--stdin") for a in rest[1:])
    ):
        return None

    run_mode = ("-r" in rest) or ("--run" in rest)
    auto_confirm = ("--auto-confirm" in rest)

    data = ""
    try:
        data = sys.stdin.read()
    except Exception:
        data = ""
    lines = [l.strip() for l in (data or "").splitlines() if l.strip()]
    text = lines[-1] if lines else ""
    if not text:
        deps.cprint(deps.Colors.RED, "❌ stdin: brak tekstu")
        return 1

    deps.nlp2cmd_prewarm_force()
    translated = deps.nlp2cmd_translate(text, config=config, force=True)
    if not translated:
        try:
            print(
                "\n".join(
                    [
                        "event:",
                        "  type: nlp2cmd",
                        f"  text: {text}",
                        "  ok: false",
                        "  reason: no_command",
                    ]
                )
            )
        except BrokenPipeError:
            return 0
        return 1

    if not run_mode:
        print(translated)
        return 0

    if dry_run:
        print(translated)
        return 0

    if not auto_confirm:
        if not deps.nlp2cmd_confirm(translated):
            return 0

    ok, reason = deps.check_command_safety(translated, config, dry_run)
    if not ok:
        return 0 if reason == "dry-run" else 1
    out, code, printed = shell.run_command_any(translated)
    if out.strip() and not printed:
        print(out, end="", flush=True)
    return code
