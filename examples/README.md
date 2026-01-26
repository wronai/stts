# stts examples

This folder contains runnable E2E (end-to-end) test scripts.

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

CI/Docker one-shot (bez mikrofonu):

```bash
STTS_MOCK_STT=1 ./python/stts --stt-file python/samples/cmd_ls.wav \
  --stt-stream-shell --cmd 'echo "{STT_STREAM}"' --dry-run
```

## Pipeline: STT → nlp2cmd (stdin)

```bash
./python/stts --stt-once | ./python/stts nlp2cmd -r stdin --auto-confirm
```

Tip (CI): wyłącz odtwarzanie audio:

```bash
export STTS_TTS_NO_PLAY=1
```

## Test Suites

| Script | Description | Requirements |
|--------|-------------|--------------|
| `e2e_stt.sh` | Tests STT providers (whisper_cpp, vosk) | `make stt-vosk-pl` |
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
