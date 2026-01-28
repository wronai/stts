from __future__ import annotations

from typing import List, Optional


def parse_args(argv: List[str]):
    stt_file = None
    stt_only = False
    stt_once = False
    stt_stream_shell = False
    stream_shell_cmd = None
    setup = False
    init = None
    tts_provider = None
    tts_voice = None
    tts_stdin = False
    tts_test = False
    tts_test_text = None
    install_piper = False
    download_piper_voice = None
    help_ = False
    dry_run = False
    safe_mode = False
    stream_cmd = None
    fast_start = None
    stt_gpu_layers = None
    stt_provider = None
    stt_model = None
    timeout_s = None
    vad_silence_ms = None
    list_stt = False
    list_tts = False
    nlp2cmd_parallel = None
    daemon_mode = False
    nlp2cmd_url = None
    nlp2cmd_timeout_s = None
    daemon_log = None
    daemon_no_execute = False
    daemon_triggers: List[str] = []
    daemon_triggers_file = None
    daemon_wake_word = None
    rest: List[str] = []

    it = iter(argv)
    for a in it:
        if a == "--stt-provider":
            stt_provider = next(it, None)
        elif a == "--stt-model":
            stt_model = next(it, None)
        elif a == "--timeout":
            try:
                timeout_s = float((next(it, None) or "").strip())
            except Exception:
                timeout_s = None
        elif a == "--vad-silence-ms":
            try:
                vad_silence_ms = int((next(it, None) or "").strip())
            except Exception:
                vad_silence_ms = None
        elif a == "--stt-file":
            stt_file = next(it, None)
        elif a == "--stt-only":
            stt_only = True
        elif a == "--stt-once":
            stt_once = True
        elif a == "--stt-stream-shell":
            stt_stream_shell = True
        elif a == "--cmd":
            stream_shell_cmd = next(it, None)
        elif a == "--setup":
            setup = True
        elif a == "--init":
            init = next(it, None)
        elif a == "--tts-provider":
            tts_provider = next(it, None)
        elif a == "--tts-voice":
            tts_voice = next(it, None)
        elif a == "--tts-stdin":
            tts_stdin = True
        elif a == "--tts-test":
            tts_test = True
            tts_test_text = next(it, None)
        elif a == "--install-piper":
            install_piper = True
        elif a == "--download-piper-voice":
            download_piper_voice = next(it, None)
        elif a == "--dry-run":
            dry_run = True
        elif a == "--safe-mode":
            safe_mode = True
        elif a == "--stream":
            stream_cmd = True
        elif a == "--no-stream":
            stream_cmd = False
        elif a == "--fast-start":
            fast_start = True
        elif a == "--full-start":
            fast_start = False
        elif a == "--stt-gpu-layers":
            try:
                stt_gpu_layers = int((next(it, None) or "0").strip())
            except Exception:
                stt_gpu_layers = 0
        elif a == "--nlp2cmd-parallel":
            nlp2cmd_parallel = True
        elif a == "--no-nlp2cmd-parallel":
            nlp2cmd_parallel = False
        elif a == "--list-stt":
            list_stt = True
        elif a == "--list-tts":
            list_tts = True
        elif a in ("--daemon", "--service"):
            daemon_mode = True
        elif a == "--nlp2cmd-url":
            nlp2cmd_url = next(it, None)
        elif a == "--nlp2cmd-timeout":
            try:
                nlp2cmd_timeout_s = float((next(it, None) or "").strip())
            except Exception:
                nlp2cmd_timeout_s = None
        elif a == "--daemon-log":
            daemon_log = next(it, None)
        elif a == "--no-execute":
            daemon_no_execute = True
        elif a == "--trigger":
            v = next(it, None)
            if v:
                daemon_triggers.append(v)
        elif a == "--triggers-file":
            daemon_triggers_file = next(it, None)
        elif a == "--wake-word":
            daemon_wake_word = next(it, None)
        elif a in ("--help", "-h"):
            help_ = True
        else:
            rest.append(a)

    return (
        stt_file,
        stt_only,
        stt_once,
        stt_stream_shell,
        stream_shell_cmd,
        setup,
        init,
        tts_provider,
        tts_voice,
        tts_stdin,
        tts_test,
        tts_test_text,
        install_piper,
        download_piper_voice,
        help_,
        dry_run,
        safe_mode,
        stream_cmd,
        fast_start,
        stt_gpu_layers,
        stt_provider,
        stt_model,
        timeout_s,
        vad_silence_ms,
        list_stt,
        list_tts,
        nlp2cmd_parallel,
        daemon_mode,
        nlp2cmd_url,
        nlp2cmd_timeout_s,
        daemon_log,
        daemon_no_execute,
        daemon_triggers,
        daemon_triggers_file,
        daemon_wake_word,
        rest,
    )
