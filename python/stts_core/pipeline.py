"""
Unified pipeline contract for STTS.

This module defines PipelineRequest/PipelineResult dataclasses and a single
run_pipeline(req) -> PipelineResult entry point that dispatches to the
appropriate pipeline mode.
"""
import contextlib
import os
import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, List, Optional

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


class PipelineMode(Enum):
    """Pipeline execution modes."""
    STT_ONCE = auto()
    STT_STREAM_SHELL = auto()
    STT_FILE_PLACEHOLDER = auto()
    STT_FILE_DEFAULT = auto()
    NLP2CMD_PARALLEL = auto()
    NLP2CMD_STDIN = auto()
    PIPE_DRY_RUN = auto()
    INTERACTIVE = auto()


@dataclass
class PipelineRequest:
    """
    Immutable request describing what the pipeline should do.
    
    Attributes:
        mode: Which pipeline mode to execute
        config: Configuration dict (from load_config)
        deps: PipelineDeps with injected callables
        shell: VoiceShell instance (or compatible)
        stt_file: Optional path to audio file for STT
        stt_only: If True, only capture STT text without execution
        dry_run: If True, print commands without executing
        rest: Remaining CLI arguments (for placeholder expansion)
        stream_shell_cmd: Command template for stream shell mode
    """
    mode: PipelineMode
    config: dict
    deps: PipelineDeps
    shell: Any  # VoiceShell
    stt_file: Optional[str] = None
    stt_only: bool = False
    dry_run: bool = False
    rest: List[str] = field(default_factory=list)
    stream_shell_cmd: Optional[str] = None


@dataclass
class PipelineResult:
    """
    Result of pipeline execution.
    
    Attributes:
        exit_code: Process exit code (0 = success)
        output: Optional captured output text
        command: Optional command that was executed
        error: Optional error message if failed
    """
    exit_code: int
    output: Optional[str] = None
    command: Optional[str] = None
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.exit_code == 0


def run_pipeline(req: PipelineRequest) -> PipelineResult:
    """
    Execute a pipeline request and return the result.
    
    This is the single entry point for all non-interactive pipeline modes.
    It dispatches to the appropriate handler based on req.mode.
    
    Args:
        req: PipelineRequest describing what to do
        
    Returns:
        PipelineResult with exit_code and optional output/error
    """
    try:
        code = _dispatch(req)
        return PipelineResult(exit_code=code if code is not None else 0)
    except KeyboardInterrupt:
        return PipelineResult(exit_code=130)
    except BrokenPipeError:
        return PipelineResult(exit_code=0)
    except Exception as e:
        return PipelineResult(exit_code=1, error=str(e))


def _dispatch(req: PipelineRequest) -> Optional[int]:
    """Internal dispatcher to existing helper functions."""
    
    if req.mode == PipelineMode.PIPE_DRY_RUN:
        return run_pipe_dry_run()
    
    if req.mode == PipelineMode.STT_ONCE:
        return run_stt_once(req.deps, req.shell, req.stt_file)
    
    if req.mode == PipelineMode.STT_STREAM_SHELL:
        return run_stt_stream_shell(
            req.deps, req.shell, req.config,
            req.stt_file, req.stream_shell_cmd, req.dry_run
        )
    
    if req.mode == PipelineMode.NLP2CMD_STDIN:
        result = run_nlp2cmd_stdin_mode(
            req.deps, req.config, req.shell, req.rest, req.dry_run
        )
        return result if result is not None else 0
    
    if req.mode == PipelineMode.NLP2CMD_PARALLEL:
        result = run_nlp2cmd_parallel_fastpath(
            req.deps, req.config, req.shell,
            req.stt_file, req.stt_only, req.dry_run, req.rest
        )
        return result if result is not None else 0
    
    if req.mode == PipelineMode.STT_FILE_PLACEHOLDER:
        return run_stt_file_placeholder_mode(
            req.deps, req.config, req.shell,
            req.stt_file, req.dry_run, req.rest
        )
    
    if req.mode == PipelineMode.STT_FILE_DEFAULT:
        return run_stt_file_default_mode(
            req.deps, req.config, req.shell,
            req.stt_file, req.stt_only, req.dry_run
        )
    
    if req.mode == PipelineMode.INTERACTIVE:
        # Interactive mode is handled by VoiceShell.run() directly
        # This is a placeholder for future refactoring
        return None
    
    return 1  # Unknown mode


def detect_pipeline_mode(
    stt_once: bool,
    stt_stream_shell: bool,
    stt_file: Optional[str],
    stt_only: bool,
    dry_run: bool,
    rest: List[str],
) -> Optional[PipelineMode]:
    """
    Detect which pipeline mode should be used based on CLI flags.
    
    Returns None if the request should fall through to interactive mode
    or other handling in main().
    """
    bin_name = os.environ.get("STTS_NLP2CMD_BIN", "nlp2cmd")
    
    # Pipe dry-run: stdin is not a TTY and --dry-run is set, no other mode flags
    if dry_run and (not sys.stdin.isatty()) and not stt_file and not stt_stream_shell and not stt_once:
        if not rest or rest[0] != bin_name:
            return PipelineMode.PIPE_DRY_RUN
    
    # STT once mode
    if stt_once:
        return PipelineMode.STT_ONCE
    
    # STT stream shell mode
    if stt_stream_shell:
        return PipelineMode.STT_STREAM_SHELL
    
    # NLP2CMD stdin mode: nlp2cmd with stdin/--stdin and piped input
    if rest and rest[0] == bin_name and (not sys.stdin.isatty()):
        if any(a in ("stdin", "--stdin") for a in rest[1:]):
            return PipelineMode.NLP2CMD_STDIN
    
    # NLP2CMD parallel fastpath: nlp2cmd with {STT} placeholder
    if rest and rest[0] == bin_name and any("{STT}" in a for a in rest):
        return PipelineMode.NLP2CMD_PARALLEL
    
    # STT file modes
    if stt_file:
        has_placeholder = any(("{STT}" in a) or ("{STT_STREAM}" in a) for a in rest)
        if has_placeholder:
            return PipelineMode.STT_FILE_PLACEHOLDER
        else:
            return PipelineMode.STT_FILE_DEFAULT
    
    return None  # Fall through to interactive or other handling
