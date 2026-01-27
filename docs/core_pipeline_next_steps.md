# Core pipeline refactor – next steps

Cel: po pierwszym rozbiciu `python/stts` doprowadzić do modularnego rdzenia pipeline i parytetu API z Node.js, bez zmiany zachowania.

## 1) Proponowany układ modułów (Python)

```
python/stts_core/
  __init__.py
  config.py          # load_config + merge env/CLI + walidacja
  contracts.py       # PipelineRequest/PipelineResult
  input_sources.py   # STT mic / STT file / stdin / placeholder
  stages/
    stt.py           # STT provider selection + listen
    normalize.py     # normalize_stt(...) (wydzielony kontrakt)
    nlp2cmd.py       # nlp2cmd translate + confirm
    execute.py       # safe-mode + dry-run + stream/no-stream
    tts.py           # auto-tts + tts stdin/test
  pipeline.py        # run_pipeline(req) -> res
```

Zasada: `python/stts` zostaje jako CLI + dispatch (bez logiki biznesowej), a `stts_core` przejmuje pipeline.

## 2) Kontrakt pipeline (propozycja)

```python
@dataclass
class PipelineRequest:
    config: dict
    mode: Literal["stt_file", "stt_once", "stt_stream_shell", "stdin", "cli"]
    stt_file: Optional[str] = None
    cmd_template: Optional[str] = None
    raw_text: Optional[str] = None
    dry_run: bool = False
    safe_mode: bool = True
    stream: bool = False

@dataclass
class PipelineResult:
    stt_text: Optional[str]
    normalized_text: Optional[str]
    translated_cmd: Optional[str]
    executed_cmd: Optional[str]
    stdout: str
    exit_code: int
    tts_text: Optional[str]
```

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
