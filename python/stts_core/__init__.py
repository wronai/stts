"""STTS Core - Core functionality for Speech-to-Text-to-Speech."""

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

from .text import TextNormalizer, normalize_stt

__all__ = [
    # Deps
    "PipelineDeps",
    # Text normalization
    "TextNormalizer",
    "normalize_stt",
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
