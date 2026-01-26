# STT providers

## Implemented (today)

STT provider można ustawić:

- przez env: `STTS_STT_PROVIDER`, `STTS_STT_MODEL`
- przez CLI (nadpisuje config/env): `--stt-provider`, `--stt-model`

Szybki check:

```bash
./stts --list-stt
```

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
STTS_DEEPGRAM_KEY=sk-... ./stts --stt-provider deepgram --stt-file python/samples/cmd_ls.wav --stt-only
```

### Vosk (`stt_provider=vosk`)

- Offline.
- Very fast and lightweight, good for RPi/CPU.
- Requires a Vosk model downloaded under `~/.config/stts-python/models/vosk/`.

Install helper (downloads Polish model):

```bash
make stt-vosk-pl
```

Use:

```bash
./stts --stt-provider vosk --stt-model small-pl --stt-file python/samples/cmd_ls.wav --stt-only
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

Already implemented in `python/stts`.
