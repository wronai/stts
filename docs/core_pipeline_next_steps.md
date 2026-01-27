# Core pipeline refactor – next steps

Cel: po pierwszym rozbiciu `python/stts` doprowadzić do modularnego rdzenia pipeline i parytetu API z Node.js, bez zmiany zachowania.

## ✅ Zrealizowane (v0.1.36)

### Struktura `stts_core`

```
python/stts_core/
  __init__.py           # eksporty publiczne
  pipeline_helpers.py   # PipelineDeps + funkcje run_* (legacy)
  pipeline_utils.py     # argv_to_cmd, expand_placeholders
  pipeline.py           # PipelineMode, PipelineRequest, PipelineResult, run_pipeline()
```

### Kontrakt pipeline (zaimplementowany)

```python
class PipelineMode(Enum):
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
    exit_code: int
    output: Optional[str] = None
    command: Optional[str] = None
    error: Optional[str] = None

def run_pipeline(req: PipelineRequest) -> PipelineResult: ...
def detect_pipeline_mode(...) -> Optional[PipelineMode]: ...
```

## 1) Dalsze kroki modularyzacji

```
python/stts_core/
  config.py          # load_config + merge env/CLI + walidacja
  input_sources.py   # STT mic / STT file / stdin / placeholder
  stages/
    stt.py           # STT provider selection + listen
    normalize.py     # normalize_stt(...) (wydzielony kontrakt)
    nlp2cmd.py       # nlp2cmd translate + confirm
    execute.py       # safe-mode + dry-run + stream/no-stream
    tts.py           # auto-tts + tts stdin/test
```

Zasada: `python/stts` zostaje jako CLI + dispatch (bez logiki biznesowej), a `stts_core` przejmuje pipeline.

## 3) Wejścia i strategie

- **STT mic / STT file** → `InputSource` zwraca `stt_text`.
- **stdin** → mapowanie ostatniej niepustej linii jako `raw_text`.
- **placeholder** → `{STT}` i `{STT_STREAM}` expand w `cmd_template`.

## 4) Wykonanie i bezpieczeństwo

- `CommandRunner`: dry-run / safe-mode / stream/no-stream.
- Jeden punkt prawdy dla `check_command_safety`.

## 5) Parytet API Python ↔ Node (lista do uzupełnienia)

- STT: `--stt-provider`, `--stt-model`, `--stt-file`, `--stt-once`, `--stt-stream-shell`
- Pipeline: `--cmd`, `--dry-run`, `--stream/--no-stream`
- NLP2CMD: `nlp2cmd`, `--nlp2cmd-url`, `--nlp2cmd-timeout`, `--nlp2cmd-parallel`
- Safety: `--safe-mode`, `STTS_DENYLIST`
- VAD/timeout: `--timeout`, `--vad-silence-ms`

Dodatkowo: spisać rozbieżności i zdecydować (dodać do Node / usunąć z opisu).

## 6) Kontrakty providerów (STT/TTS)

Ujednolicić w Python/Node metadane:

- `name`, `language`, `default_model`, `supports_stream`, `requires_gpu`, `notes`
- standardowe `is_available(info)` + komunikat diagnostyczny

## 7) Testy regresji

- jednostkowe testy `pipeline.run_pipeline` na mockach (STT/TTS/NLP2CMD)
- E2E: `--dry-run` + `stdin`, `--stt-file` placeholder, `--safe-mode` denylist
- snapshot testy kontraktu wyniku pipeline
