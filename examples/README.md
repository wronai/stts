# stts examples

This folder contains runnable E2E (end-to-end) test scripts.

Provider docs:

- [stt_providers.md](../docs/stt_providers.md)
- [tts_providers.md](../docs/tts_providers.md)

## Quick Start

```bash
# Run all tests
bash examples/e2e_all.sh

# Run specific test suite
bash examples/e2e_stt.sh       # STT providers only
bash examples/e2e_tts.sh       # TTS providers only
bash examples/e2e_pipeline.sh  # Full STT+TTS+execution
bash examples/e2e_streaming.sh # Streaming modes
```

## Placeholder shell (voice-driven REPL)

Python-only:

```bash
./python/stts --stt-stream-shell --cmd 'nlp2cmd -r --query "{STT}" --auto-confirm'
```

## Wrapper: `{STT}` + nlp2cmd (quoting + debug)

Najprostszy wariant (STT → nlp2cmd):

```bash
STTS_NLP2CMD_ENABLED=1 ./python/stts nlp2cmd -r --query "{STT}" --auto-confirm
```

Debug (zobacz co dokładnie zostanie uruchomione po podstawieniu `{STT}`):

```bash
STTS_NLP2CMD_ENABLED=1 ./python/stts --dry-run nlp2cmd -r --query "{STT}" --auto-confirm
```

Gotowy skrypt (mock STT, bez mikrofonu):

```bash
bash examples/nlp2cmd_placeholder.sh
```

CI/Docker one-shot (bez mikrofonu):

```bash
STTS_MOCK_STT=1 ./python/stts --stt-file python/samples/cmd_ls.wav \
  --stt-stream-shell --cmd 'echo "{STT_STREAM}"' --dry-run
```

## Pipeline: STT → nlp2cmd (stdin)

```bash
./python/stts --stt-once | ./python/stts nlp2cmd -r stdin --auto-confirm
```

## Daemon Mode: Wake-word + nlp2cmd Service

Tryb ciągłego nasłuchiwania z wake-word "hejken" i integracją z nlp2cmd HTTP service.

**Terminal 1: uruchom nlp2cmd service**

```bash
cd /home/tom/github/wronai/nlp2cmd
nlp2cmd service --host 0.0.0.0 --port 8008
```

**Terminal 2: uruchom stts daemon**

```bash
./python/stts --daemon --nlp2cmd-url http://localhost:8008
```

Lepsza jakość STT (offline):

```bash
./python/stts --daemon --nlp2cmd-url http://localhost:8008 --stt-provider whisper_cpp --stt-model medium
```

Uwaga: przy pierwszym uruchomieniu może pobierać model (np. `medium` ~ 1.5 GB).

Gotowy skrypt:

```bash
bash examples/daemon_nlp2cmd.sh
```

### Opcje daemon mode

| Opcja | Opis |
|-------|------|
| `--daemon` / `--service` | Uruchom w trybie ciągłego nasłuchiwania |
| `--nlp2cmd-url URL` | URL serwisu nlp2cmd (domyślnie: `http://localhost:8000`) |
| `--daemon-log FILE` | Zapisz logi do pliku |
| `--no-execute` | Tylko tłumacz (nie wykonuj komend) |
| `--stt-provider NAME` | Wybór STT (np. `whisper_cpp`, `vosk`, `deepgram`) |
| `--stt-model VALUE` | Model STT (np. `medium` dla whisper.cpp) |

### Przykłady użycia (mów do mikrofonu)

- "hejken lista folderów"
- "hejken pokaż wszystkie procesy"
- "hejken uruchom docker"
- "hey ken znajdź pliki większe niż 100MB"

Tip (CI): wyłącz odtwarzanie audio:

```bash
export STTS_TTS_NO_PLAY=1
```

## Test Suites

| Script | Description | Requirements |
|--------|-------------|--------------|
| `e2e_stt.sh` | Tests STT providers (whisper_cpp, vosk, optional faster_whisper) | `make stt-vosk-pl` |
| `e2e_tts.sh` | Tests TTS providers (piper, espeak) | `make tts-piper-pl` |
| `e2e_pipeline.sh` | Full pipeline: STT → Execute → TTS | Both STT+TTS |
| `e2e_streaming.sh` | Streaming input/output modes | Basic setup |
| `e2e_offline.sh` | Deterministic offline tests (mocked) | None |
| `e2e_deepgram.sh` | Online Deepgram STT | `STTS_DEEPGRAM_KEY` |
| `e2e_all.sh` | Runs all test suites | All providers |

## Prerequisites

```bash
# Install local STT+TTS stack
make setup-local-full

# Or install individually
make stt-vosk-pl     # Vosk + Polish model
make tts-piper-pl    # Piper + Polish voices

# Activate venv
source venv/bin/activate
```

## Expected Output

```
╔════════════════════════════════════════════╗
║       STTS E2E Test Suite                  ║
╚════════════════════════════════════════════╝

▶ Running: STT Tests
[whisper_cpp basic] ✅ PASS
[vosk basic] ✅ PASS
...

▶ Running: TTS Tests
[piper basic] ✅ PASS
[espeak basic] ✅ PASS
...

╔════════════════════════════════════════════╗
║  ✅ All E2E test suites completed          ║
╚════════════════════════════════════════════╝
```
