# E2E tests

## Offline (deterministic, recommended for CI)

The project uses WAV fixtures + sidecar transcripts:

- `samples/*.wav`
- `samples/*.wav.txt`

When you set `STTS_MOCK_STT=1`, STTS reads `*.wav.txt` instead of running a real STT model.

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

## Offline placeholder loop (Python)

```bash
STTS_MOCK_STT=1 ./stts --stt-file python/samples/cmd_echo_hello.wav \
  --stt-stream-shell --cmd "echo '{STT_STREAM}'" --dry-run
```

## Optional online (Deepgram)

This runs only when `STTS_DEEPGRAM_KEY` is set.

```bash
STTS_DEEPGRAM_KEY=sk-... STTS_STT_PROVIDER=deepgram ./stts --stt-file python/samples/cmd_ls.wav --stt-only
```
