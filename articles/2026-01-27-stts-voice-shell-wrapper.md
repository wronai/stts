---
title: "STTS: Voice Shell Wrapper - Stan Projektu Styczeń 2026"
date: 2026-01-27
author: "Softreck Team"
categories:
  - Projekty
  - Voice Computing
  - DevOps Automation
tags:
  - stts
  - speech-to-text
  - text-to-speech
  - voice-interface
  - nlp2cmd
featured_image: /assets/images/stts-pipeline.png
excerpt: "STTS to głosowy wrapper dla shella łączący STT/TTS z NLP2CMD. Poznaj jak sterować terminalem głosem."
status: published
---

# STTS: Voice Shell Wrapper - Stan Projektu Styczeń 2026

## 📊 Podsumowanie

STTS (Speech-To-Text-Shell) to pythonowy wrapper umożliwiający sterowanie terminalem za pomocą głosu. Łączy rozpoznawanie mowy (STT), syntezę mowy (TTS) i integrację z NLP2CMD.

| Metryka | Wartość |
|---|---|
| Wersja | MVP |
| Język | Python 3.10+ |
| STT Providers | 3 (whisper_cpp, vosk, deepgram) |
| TTS Providers | 2 (espeak, piper) |
| Obsługiwane języki | Polski, Angielski |

## 🎙️ Jak to działa?

```text
┌─────────────────┐
│   Mikrofon      │  Mówisz: "Pokaż pliki Python"
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   STT Engine    │  whisper_cpp / vosk / deepgram
└────────┬────────┘
         │ "pokaż pliki python"
         ▼
┌─────────────────┐
│   NLP2CMD       │  → find . -name "*.py"
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Wykonanie     │  Shell wykonuje komendę
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   TTS Engine    │  piper / espeak
└─────────────────┘
         │
         ▼
      🔊 "Znaleziono 42 pliki"
```

## 🚀 Szybki start

### Instalacja

```bash
# Klonuj repo
git clone https://github.com/softreck/stts
cd stts/python

# Konfiguracja
cp .env.example .env
./stts --setup

# Inicjalizacja whisper_cpp
./stts --init whisper_cpp:tiny
```

### Podstawowe użycie

```bash
# Tryb interaktywny (voice shell)
./stts

# Jednorazowe rozpoznanie
./stts --stt-once

# Test TTS
./stts --tts-test "Cześć, to działa!"

# Z NLP2CMD
./stts nlp2cmd -r --query "{STT}" --auto-confirm
```

## 📊 Benchmark Wydajności

Wyniki z `./examples/benchmark.sh`:

### STT (Speech-to-Text)

| Provider | Model | Avg Latency | P95 | GPU |
|---|---|---:|---:|---|
| whisper_cpp | tiny | 0.71s | 0.75s | Opcjonalnie |
| vosk | small-pl | 1.17s | 1.29s | Nie |
| deepgram | nova-2 | 0.45s | 0.52s | Cloud |

### TTS (Text-to-Speech)

| Provider | Voice | Avg Latency | Jakość |
|---|---|---:|---|
| piper | pl_PL-gosia-medium | 0.48s | ⭐⭐⭐⭐⭐ |
| espeak | pl | 0.12s | ⭐⭐⭐ |

### Pipeline STT→TTS

| Kombinacja | Avg Total | P95 |
|---|---:|---:|
| whisper + piper | 1.19s | 1.32s |
| whisper + espeak | 0.91s | 1.03s |
| vosk + piper | 1.67s | 1.85s |

## 🔧 Konfiguracja

### Plik .env

```bash
# STT
STTS_STT_PROVIDER=whisper_cpp
STTS_STT_MODEL=tiny
STTS_STT_GPU_LAYERS=35  # dla GPU

# TTS
STTS_TTS_PROVIDER=piper
STTS_TTS_VOICE=pl_PL-gosia-medium

# NLP2CMD Integration
STTS_NLP2CMD_ENABLED=1
STTS_NLP2CMD_PARALLEL=1
STTS_NLP2CMD_CONFIRM=1

# Inne
STTS_TIMEOUT=5
STTS_STREAM=1
STTS_FAST_START=1
```

### GPU Acceleration (whisper.cpp + CUDA)

```bash
STTS_GPU_ENABLED=1 ./stts --setup
./stts --stt-gpu-layers 35
```

## 🇵🇱 Wsparcie dla polskiego

**STT**
- vosk: Model vosk-model-small-pl (~50MB)
- whisper: Automatyczna detekcja języka
- deepgram: STTS_LANGUAGE=pl

**TTS**
- piper: pl_PL-gosia-medium (neural, najlepsza jakość)
- espeak: pl (szybki, gorsza jakość)

## 📡 Integracja z NLP2CMD

### Tryb usługi HTTP

```bash
# Start NLP2CMD jako usługę
nlp2cmd service --host 127.0.0.1 --port 8000

# One-liner: STT → HTTP → komenda
./stts --stt-once | \
  jq -Rs '{query: ., dsl: "auto"}' | \
  curl -sS http://127.0.0.1:8000/query \
    -H 'Content-Type: application/json' \
    -d @- | \
  jq -r '.command'
```

### Voice-driven REPL

```bash
./stts --stt-stream-shell --cmd 'nlp2cmd -r --query "{STT}" --auto-confirm'
```

## 🐳 Docker

```bash
# Build
make docker-build

# Test (bez mikrofonu)
make docker-test

# Interaktywnie (z audio)
docker run --rm -it \
  --device /dev/snd \
  -e PULSE_SERVER=unix:/tmp/pulse/native \
  -v $XDG_RUNTIME_DIR/pulse/native:/tmp/pulse/native \
  stts-python:latest
```

## 🚧 Plany rozwoju

### Q1 2026

| Funkcjonalność | Priorytet | Status |
|---|---|---|
| Refaktoryzacja na moduły | P0 | 🚧 |
| Streaming STT (VAD) | P1 | Planowane |
| Plugin system | P1 | Planowane |
| Auto-language detection | P2 | Planowane |

### Planowana struktura po refaktoryzacji

```text
stts/
├── src/stts/
│   ├── cli.py
│   ├── config.py
│   ├── stt/
│   │   ├── whisper_cpp.py
│   │   ├── vosk.py
│   │   └── deepgram.py
│   ├── tts/
│   │   ├── espeak.py
│   │   └── piper.py
│   └── audio/
│       ├── recorder.py
│       └── player.py
└── tests/
```

## 📚 Zasoby

- GitHub: https://github.com/softreck/stts
- NLP2CMD: https://github.com/softreck/nlp2cmd
- Piper TTS: https://github.com/rhasspy/piper
- Whisper.cpp: https://github.com/ggerganov/whisper.cpp

## 🤝 Jak pomóc?

- Testuj - szczególnie polskie komendy głosowe
- Zgłaszaj problemy - audio, latency, accuracy
- Kontrybuuj - nowe providery STT/TTS

```bash
git clone https://github.com/softreck/stts
cd stts/python
./stts --setup
./stts
```

*Artykuł zaktualizowany: 27 stycznia 2026*
