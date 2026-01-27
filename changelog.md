# Changelog

## 0.1.32

- Added: `faster_whisper` STT provider (Python) with tuning via `STTS_FASTER_WHISPER_DEVICE` and `STTS_FASTER_WHISPER_COMPUTE_TYPE`.
- Added: `docs/tts_providers.md` and refreshed `docs/stt_providers.md`.
- Added: provider-level tests (`python/tests/test_providers.py`).
- Changed: examples/benchmark can optionally include `faster_whisper` via `STTS_BENCH_INCLUDE_FASTER_WHISPER=1`.

## 0.1.20

- Added: `--stream/--no-stream` and `STTS_STREAM` to stream command output (better interactivity).
- Added: `--fast-start/--full-start` and `STTS_FAST_START` for faster startup by skipping expensive system checks.
- Added: `--list-tts` to list available TTS providers.
- Added: additional TTS providers (depending on platform availability): `spd-say`, `flite`, `say` (macOS), plus improved `piper` handling.
- Changed: Piper auto-install/auto-download in Python is lazy (triggered on first `speak()`), improving cold start.
- Added: whisper.cpp GPU support configuration:
  - `--stt-gpu-layers N`
  - `STTS_STT_GPU_LAYERS`
  - `STTS_GPU_ENABLED=1` to force CUDA build when installing whisper.cpp (if `nvcc` is available)
- Fixed: streaming execution no longer uses login shell (`bash -lc`), avoiding noisy environment banners.

