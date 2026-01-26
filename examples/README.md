# stts examples

This folder contains runnable E2E (end-to-end) test scripts.

## Quick Start

```bash
# Run all tests
./examples/e2e_all.sh

# Run specific test suite
./examples/e2e_stt.sh       # STT providers only
./examples/e2e_tts.sh       # TTS providers only
./examples/e2e_pipeline.sh  # Full STT+TTS+execution
./examples/e2e_streaming.sh # Streaming modes
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
