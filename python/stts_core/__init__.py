from .pipeline_helpers import (
    PipelineDeps,
    run_nlp2cmd_parallel_fastpath,
    run_nlp2cmd_stdin_mode,
    run_pipe_dry_run,
    run_stt_file_default_mode,
    run_stt_file_placeholder_mode,
    run_stt_once,
    run_stt_stream_shell,
)

from .pipeline import (
    PipelineMode,
    PipelineRequest,
    PipelineResult,
    run_pipeline,
    detect_pipeline_mode,
)

from .shell import VoiceShell

__all__ = [
    # Deps
    "PipelineDeps",
    # Shell
    "VoiceShell",
    # Pipeline contract
    "PipelineMode",
    "PipelineRequest",
    "PipelineResult",
    "run_pipeline",
    "detect_pipeline_mode",
    # Legacy helpers (for backward compat)
    "run_nlp2cmd_parallel_fastpath",
    "run_nlp2cmd_stdin_mode",
    "run_pipe_dry_run",
    "run_stt_file_default_mode",
    "run_stt_file_placeholder_mode",
    "run_stt_once",
    "run_stt_stream_shell",
]
