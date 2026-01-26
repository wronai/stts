# E2E tests

## Offline (deterministic, recommended for CI)

The project uses WAV fixtures + sidecar transcripts:

- `samples/*.wav`
- `samples/*.wav.txt`

When you set `STTS_MOCK_STT=1`, STTS reads `*.wav.txt` instead of running a real STT model.

Tip (CI/Docker): jeśli nie chcesz odtwarzania audio (TTS), ustaw `STTS_TTS_NO_PLAY=1`.

Run via make:

```bash
make docker-test-python
make docker-test-nodejs
```

Or directly:

```bash
bash python/tests/docker_test.sh
bash nodejs/tests/docker_test.sh
```

## Local E2E suites (examples/)

The repository also contains convenience scripts under `examples/`.

```bash
bash examples/e2e_all.sh
```

Or run a single suite:

```bash
bash examples/e2e_stt.sh
bash examples/e2e_tts.sh
bash examples/e2e_pipeline.sh
bash examples/e2e_streaming.sh
```

## Offline placeholder loop (Python)

```bash
STTS_MOCK_STT=1 ./stts --stt-file python/samples/cmd_echo_hello.wav \
  --stt-stream-shell --cmd "echo '{STT_STREAM}'" --dry-run
```

## Offline placeholder one-shot (Python, bez pętli)

Jeśli podasz `--stt-file` oraz komendę zawierającą `{STT}` / `{STT_STREAM}`, `stts` uruchomi STT z pliku i podstawia placeholdery.

```bash
STTS_MOCK_STT=1 ./stts --stt-file python/samples/cmd_ls.wav --dry-run echo '{STT}'
```

## Offline pipeline: STT → nlp2cmd (stdin)

```bash
STTS_MOCK_STT=1 ./stts --stt-file python/samples/cmd_ls.wav --stt-only | \
  ./stts nlp2cmd -r stdin --auto-confirm --dry-run
```

## Optional online (Deepgram)

This runs only when `STTS_DEEPGRAM_KEY` is set.

```bash
STTS_DEEPGRAM_KEY=sk-... ./stts --stt-provider deepgram --stt-file python/samples/cmd_ls.wav --stt-only
```

## Benchmark (optional)

Quick local performance/accuracy matrix (STT + TTS):

```bash
bash examples/benchmark.sh
```
