# STT providers

## Implemented (today)

### whisper.cpp (`stt_provider=whisper_cpp`)

- Offline.
- Good default for Docker/CI and local usage.
- Models are downloaded under `~/.config/stts-python/models/whisper.cpp/`.

### Deepgram (`stt_provider=deepgram`)

- Online (REST, file-based transcription).
- Requires `STTS_DEEPGRAM_KEY`.
- Optional: set `STTS_DEEPGRAM_MODEL` (default `nova-2`).

Example:

```bash
STTS_DEEPGRAM_KEY=sk-... STTS_STT_PROVIDER=deepgram ./stts --stt-file python/samples/cmd_ls.wav --stt-only
```

## Optional / roadmap (not implemented in stts yet)

The items below are intentionally marked as *not implemented* in this repository right now. They are good candidates for real-time (<500ms) streaming STT.

### faster-whisper / Distil-Whisper

- Package: `faster-whisper`
- Candidate models:
  - `distil-large-v3` (GPU)
  - `tiny` / `base` (CPU / RPi)

Suggested approach:

- Add a new provider (e.g. `stt_provider=faster_whisper`).
- Add a streaming mode that reads 100–200ms audio chunks and emits partial captions.

### whisper.cpp streaming (`stream` binary)

- whisper.cpp has a `stream` binary.
- Would require adding a new codepath to run it and parse partial output.

### Vosk

- Good for small devices (RPi).
- Would require adding a new provider and model download instructions.
