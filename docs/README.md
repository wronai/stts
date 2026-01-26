# stts documentation

This repository contains two implementations:

- `python/` – Python CLI
- `nodejs/` – Node.js CLI

Additional documents:

- `docs/stt_providers.md` – STT providers (what is implemented today + optional/roadmap ideas)
- `docs/e2e_tests.md` – how to run repeatable E2E tests (offline + optional online)

Key features (Python):

- Placeholder wrapper: `{STT}` / `{STT_STREAM}`
- Voice-driven REPL: `--stt-stream-shell --cmd '...{STT}...'`
- STT selection: `--stt-provider`, `--stt-model`, `--list-stt` (or env: `STTS_STT_PROVIDER`, `STTS_STT_MODEL`)
- Optional online STT: `deepgram` (env: `STTS_DEEPGRAM_KEY`)
- CI-friendly TTS: disable playback with `STTS_TTS_NO_PLAY=1`

Examples:

- `examples/README.md`
- `examples/e2e_offline.sh`
- `examples/e2e_deepgram.sh`
- `examples/e2e_all.sh`
- `examples/benchmark.sh`
