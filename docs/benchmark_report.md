# STTS Benchmark Report (STT/TTS Performance Matrix)

## Run command

```bash
make benchmark-report
```

Or directly:

```bash
STTS_BENCH_WARMUP=1 STTS_BENCH_ITERS=3 ./examples/benchmark.sh
```

## Environment / notes

- Benchmark default sets `STTS_TTS_NO_PLAY=1` (measures synthesis time without audio playback).
- Samples: `python/samples/*.wav` with `.wav.txt` sidecars as ground-truth where available.
- Accuracy (WER/CER) here is computed on repo samples (often synthetic / TTS-generated). Treat it as a regression/pipeline signal, not a microphone-quality benchmark.

## STT Benchmark (per-sample)

| Provider | Sample | Time (s) | WER | CER | Sim | Transcription |
|---|---|---:|---:|---:|---:|---|
| `whisper_cpp` | `cmd_echo_hello` | 0.73 | 1.0000 | 1.0000 | 0.0000 | `[MUZYKA]` |
| `whisper_cpp` | `cmd_ls` | 0.76 | 1.0000 | 3.0000 | 0.0000 | `[MUZYKA]` |
| `whisper_cpp` | `cmd_make_build` | 0.79 | 1.0000 | 0.5000 | 0.5714 | `Maka Bóliot` |
| `vosk` | `cmd_echo_hello` | 1.13 | 0.5000 | 0.5000 | 0.6667 | `hello` |
| `vosk` | `cmd_ls` | 1.15 | 1.0000 | 2.0000 | 0.2857 | `wiele` |
| `vosk` | `cmd_make_build` | 1.42 | 1.5000 | 0.8000 | 0.3333 | `był i od` |

## TTS Benchmark (per-phrase)

| Provider | Voice | Phrase (truncated) | Time (s) |
|---|---|---|---:|
| `piper` | `pl` | `Cześć, to jest test` | 0.44 |
| `piper` | `pl` | `Szybki brązowy lis przeskoczył przez p...` | 0.49 |
| `piper` | `pl` | `Jeden dwa trzy cztery pięć` | 0.49 |
| `espeak` | `pl` | `Cześć, to jest test` | 0.13 |
| `espeak` | `pl` | `Szybki brązowy lis przeskoczył przez p...` | 0.13 |
| `espeak` | `pl` | `Jeden dwa trzy cztery pięć` | 0.13 |

## STT→TTS Pipeline Matrix (per-sample)

Testing: audio → STT → transcription → TTS → speak

| STT | TTS | Sample | Total (s) | WER | Text |
|---|---|---|---:|---:|---|
| `whisper_cpp` | `piper` | `cmd_echo_hello` | 1.15 | 1.0000 | `[MUZYKA]` |
| `whisper_cpp` | `piper` | `cmd_ls` | 1.22 | 1.0000 | `[MUZYKA]` |
| `whisper_cpp` | `piper` | `cmd_make_build` | 1.24 | 1.0000 | `Maka Bóliot` |
| `whisper_cpp` | `espeak` | `cmd_echo_hello` | 0.84 | 1.0000 | `[MUZYKA]` |
| `whisper_cpp` | `espeak` | `cmd_ls` | 0.87 | 1.0000 | `[MUZYKA]` |
| `whisper_cpp` | `espeak` | `cmd_make_build` | 0.91 | 1.0000 | `Maka Bóliot` |
| `vosk` | `piper` | `cmd_echo_hello` | 1.63 | 0.5000 | `hello` |
| `vosk` | `piper` | `cmd_ls` | 1.62 | 1.0000 | `wiele` |
| `vosk` | `piper` | `cmd_make_build` | 1.86 | 1.5000 | `był i od` |
| `vosk` | `espeak` | `cmd_echo_hello` | 1.29 | 0.5000 | `hello` |
| `vosk` | `espeak` | `cmd_ls` | 1.49 | 1.0000 | `wiele` |
| `vosk` | `espeak` | `cmd_make_build` | 1.60 | 1.5000 | `był i od` |

## Round-robin STT×TTS Pipeline (alternating)

Config: `iters=3`, `warmup=1`

| STT | TTS | avg (s) | p95 (s) | WER (avg) |
|---|---|---:|---:|---:|
| `whisper_cpp` | `piper` | 1.1493 | 1.1871 | 1.0000 |
| `whisper_cpp` | `espeak` | 0.8546 | 0.9362 | 1.0000 |
| `vosk` | `piper` | 1.5913 | 1.8098 | 1.0000 |
| `vosk` | `espeak` | 1.3038 | 1.4798 | 1.0000 |

## Summary statistics

### STT Times (avg,p50,p95,min,max)

| Provider | avg | p50 | p95 | min | max |
|---|---:|---:|---:|---:|---:|
| `whisper_cpp` | 0.7607 | 0.7631 | 0.7907 | 0.7285 | 0.7907 |
| `vosk` | 1.2342 | 1.1517 | 1.4182 | 1.1327 | 1.4182 |

### STT WER (avg,p50,p95,min,max)

| Provider | avg | p50 | p95 | min | max |
|---|---:|---:|---:|---:|---:|
| `whisper_cpp` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| `vosk` | 1.0000 | 1.0000 | 1.5000 | 0.5000 | 1.5000 |

### TTS Times (avg,p50,p95,min,max)

| Provider | avg | p50 | p95 | min | max |
|---|---:|---:|---:|---:|---:|
| `piper` | 0.4735 | 0.4884 | 0.4888 | 0.4432 | 0.4888 |
| `espeak` | 0.1334 | 0.1343 | 0.1346 | 0.1314 | 0.1346 |

## Artifacts

- CSV: `/tmp/stts_benchmark_1845711/results.csv`
