import contextlib
import os
import subprocess
import sys
import shlex


def argv_to_cmd(args):
    if os.name == "nt":
        return subprocess.list2cmdline([str(a) for a in (args or [])])
    try:
        return " ".join(shlex.quote(str(a)) for a in (args or []))
    except Exception:
        return " ".join(str(a) for a in (args or []))


def expand_placeholders(deps, args, shell, config, stt_file=None):
    expanded = []
    stt_used = False

    needs_stt = any(("{STT}" in a) or ("{STT_STREAM}" in a) for a in args)
    text = None
    if needs_stt:
        stt_used = True
        with contextlib.redirect_stdout(sys.stderr):
            text = shell.listen(stt_file=stt_file) if stt_file else shell.listen()
        if not text:
            deps.cprint(deps.Colors.RED, "❌ No speech input captured")
            return None

    for arg in args:
        if text is not None:
            expanded_arg = arg.replace("{STT}", text).replace("{STT_STREAM}", text)
            expanded.append(expanded_arg)
        else:
            expanded.append(arg)

    if stt_used and config.get("auto_tts", True) and shell.tts:
        cmd = deps.argv_to_cmd(expanded)
        shell.tts.speak(cmd[:200])

    return expanded
