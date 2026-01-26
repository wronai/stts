# 🎙️ stts - Universal Voice Shell

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![Node.js Version](https://img.shields.io/badge/node.js-18+-green.svg)](https://nodejs.org)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey.svg)](https://github.com/wronai/stts)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://github.com/wronai/stts)

## 📋 Menu

- [🚀 Szybki start](#szybki-start)
- [⚙️ Konfiguracja](#konfiguracja)
- [✨ Funkcje](#-funkcje)
- [📊 Wymagania sprzętowe](#-wymagania-sprzętowe)
- [💻 Użycie](#-użycie)
- [🔧 Providery](#-providery)
- [🍓 Raspberry Pi](#-raspberry-pi)
- [🐛 Troubleshooting](#-troubleshooting)
- [📁 Struktura](#-struktura)
- [📚 Dokumentacja](#-dokumentacja)
- [🔗 Powiązane projekty](#-powiązane-projekty)

Repo zostało podzielone na **dwa niezależne projekty**:

- **`python/`** - wersja Python
- **`nodejs/`** - wersja Node.js (ESM)

Każdy folder ma własne:

- `README.md`
- `Makefile`
- `Dockerfile`
- testy Docker (bez mikrofonu)

## Szybki start


użycie STT i TTS w komendzie shell:

```bash
#tylko STT
./stts git commit -m "{STT}"
# razem z TTS 
./stts git commit -m "{STT}" | ./stts --tts-stdin
# z TTS espeak angielski
./stts git commit -m "{STT}" | ./stts --tts-stdin --tts-provider espeak --tts-voice en
# z konfiguracją TTS lepszej jakosci
./stts git commit -m "{STT}" | ./stts --tts-provider piper --tts-voice en_US-amy-medium --tts-stdin
# z konfiguracją TTS polski lepszej jakosci
./stts git commit -m "{STT}" | ./stts --tts-provider piper --tts-voice pl_PL-gosia-medium --tts-stdin
```

```bash
# GPU + szybki start
STTS_GPU_ENABLED=1 STTS_FAST_START=1 ./stts

# CPU-only z mniejszym modelem
./stts --init whisper_cpp:tiny
```

Uruchamianie komend shell nawet z błędami fonetycznymi za pomocą nlp2cmd:
```bash
./stts nlp2cmd -r "{STT}" --auto-confirm | ./stts --tts-stdin
```

output
```bash
[13:14:01] 🎤 Mów (max 5s, VAD)... ✅ VAD stop (3.4s / 3.7s)
🔎 audio: 3.4s, rms=-37.4dBFS
[13:14:05] 🔄 Rozpoznawanie... ✅ "lista folderów" (5.5s)
╭─────────────────────────────────────────────────────────────────────────────────────────────────────────────── 🚀 Run Mode ────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ lista folderów                                                                                                                                                                                                                             │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

Generating command...
Detected: shell/list

$ ls -la .
  total 108
  drwxrwxr-x 10 tom tom  4096 Jan 24 13:13 .
  drwxrwxr-x 31 tom tom  4096 Jan 24 09:33 ..
  -rw-r--r--  1 tom tom  1512 Jan 24 12:12 .env.example
  drwxrwxr-x  7 tom tom  4096 Jan 24 13:06 .git
  -rw-r--r--  1 tom tom  1664 Jan 24 10:34 .gitignore
  drwxrwxr-x  3 tom tom  4096 Jan 24 12:29 .idea
  -rw-rw-r--  1 tom tom 11357 Jan 24 09:33 LICENSE
  -rw-r--r--  1 tom tom  4658 Jan 24 12:21 Makefile
  -rw-rw-r--  1 tom tom 12421 Jan 24 13:13 README.md
  -rw-r--r--  1 tom tom     7 Jan 24 13:05 VERSION
  -rw-r--r--  1 tom tom  2291 Jan 24 12:20 bump_version.py
  drwxrwxr-x  2 tom tom  4096 Jan 24 13:05 dist
  drwxrwxr-x  5 tom tom  4096 Jan 24 10:38 nodejs
  -rw-r--r--  1 tom tom   300 Jan 24 13:05 package.json
  -rw-r--r--  1 tom tom   514 Jan 24 13:05 pyproject.toml
  drwxr-xr-x  7 tom tom  4096 Jan 24 10:43 python
  drwxr-xr-x  2 tom tom  4096 Jan 24 10:57 scripts
  -rwxr-xr-x  1 tom tom   573 Jan 24 10:11 stts
  drwxrwxr-x  2 tom tom  4096 Jan 24 13:05 stts.egg-info
  -rwxr-xr-x  1 tom tom   462 Jan 24 10:11 stts.mjs
  drwxrwxr-x  5 tom tom  4096 Jan 24 10:56 venv
✓ Command completed in 9.1ms
[stts] TTS: provider=piper voice=en_US-amy-medium
```

**Uwaga:** Domyślnie output komend może być buforowany (w zależności od trybu). Jeśli chcesz **zawsze widzieć output na żywo**, użyj `--stream` albo ustaw `STTS_STREAM=1`.

```bash
./stts git commit -m "{STT}" | ./stts --tts-stdin
[12:23:19] 🎤 Mów (max 5s, VAD)... ✅ VAD stop (4.4s / 4.6s)
🔎 audio: 4.4s, rms=-44.5dBFS
[12:23:24] 🔄 Rozpoznawanie... ✅ "Aktualizuj dokumentację." (5.7s)
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean

[stts] TTS: provider=piper voice=pl_PL-gosia-medium
```
## Konfiguracja

```bash
# Python
cd python
cp .env.example .env
./stts --setup
./stts

# Node.js
cd nodejs
cp .env.example .env
./stts.mjs --setup
./stts.mjs
```

Szybki setup (bez interakcji, Python):

```bash
./stts --init whisper_cpp:tiny
```


## .env (ustawienia / linki / domyślne wartości)

W repo jest `/.env.example` (oraz osobne `python/.env.example`, `nodejs/.env.example`).
Skrypty automatycznie wczytują `.env`.

Najważniejsze zmienne:

- `STTS_CONFIG_DIR` - katalog na modele/cache (również dla Docker volume)
- `STTS_TIMEOUT` - czas nagrywania STT (sekundy), domyślnie `5`
- `STTS_NLP2CMD_ENABLED=1` - włącza NL → komenda przez `nlp2cmd`
- `STTS_NLP2CMD_ARGS=-r` - tryb jak w przykładach: `nlp2cmd -r "Pokaż użytkowników"`
- `STTS_NLP2CMD_CONFIRM=1` - pytaj o potwierdzenie przed wykonaniem
- `STTS_PIPER_AUTO_INSTALL=1` - auto-instalacja piper binarki (Python)
- `STTS_PIPER_AUTO_DOWNLOAD=1` - auto-download modelu głosu piper (Python)
- `STTS_STREAM=1` - strumieniuj output komend (bez buforowania)
- `STTS_FAST_START=1` - szybszy start (mniej detekcji sprzętu)
- `STTS_STT_GPU_LAYERS=35` - whisper.cpp: liczba warstw na GPU (`-ngl`, wymaga build GPU)
- `STTS_GPU_ENABLED=1` - wymuś budowę whisper.cpp z CUDA przy instalacji
- `STTS_PIPER_RELEASE_TAG=2023.11.14-2` - wersja piper do pobrania
- `STTS_PIPER_VOICE_VERSION=v1.0.0` - wersja głosów piper do pobrania

## NLP2CMD (Natural Language → komendy)

W wersji Python i Node możesz:

- wpisać: `nlp Pokaż użytkowników`
- albo użyć STT: ENTER → powiedz tekst → skrypt odpali `nlp2cmd` i zapyta o potwierdzenie

Instalacja `nlp2cmd`:

```bash
cd python && make pip-nlp2cmd
```

## TTS: szybki setup + autodiagnostyka (Python)

Jeśli "TTS nie działa" (cisza), najczęstsze przyczyny:

- brak binarki providera (`espeak` / `piper`)
- dla `piper`: brak modelu `*.onnx` **i** `*.onnx.json`
- brak odtwarzacza audio (`paplay` / `aplay` / `play`) dla `piper`

### Test TTS (bez STT)

```bash
./stts --tts-test "Test syntezatora mowy"
```

### Setup: espeak (Linux)

```bash
make tts-setup-espeak
```

### Setup: piper (Linux, auto-download)

```bash
make tts-setup-piper
```

### Piper: automatyczny install + auto-download w runtime

Wersja Python potrafi automatycznie:

- pobrać binarkę `piper` do `~/.config/stts-python/bin/`
- pobrać model i config głosu do `~/.config/stts-python/models/piper/`

Ręcznie (CLI):

```bash
./stts --install-piper
./stts --download-piper-voice pl_PL-gosia-medium
./stts --tts-provider piper --tts-voice pl_PL-gosia-medium
./stts --tts-test "Cześć, to działa."
```

## Testy w Docker (bez dostępu do audio)

Testy działają przez **symulację wypowiedzi usera**:

1. Generujemy próbki audio do plików `samples/*.wav`
2. Do każdej próbki zapisujemy transkrypt w `samples/*.wav.txt`
3. W testach ustawiamy `STTS_MOCK_STT=1` i uruchamiamy `--stt-file ...`

```bash
# wszystkie platformy
make test-docker

# albo osobno
make docker-test-python
make docker-test-nodejs
```

Testy Docker montują cache/config jako volume (żeby nie pobierać modeli za każdym razem).
Domyślne katalogi cache:

- `CACHE_DIR_PYTHON=~/.config/stts-python`
- `CACHE_DIR_NODEJS=~/.config/stts-nodejs`

Możesz je nadpisać:

```bash
make test-docker CACHE_DIR_PYTHON=/tmp/stts-python-cache CACHE_DIR_NODEJS=/tmp/stts-nodejs-cache
```

Alternatywnie (wrapper shell):

```bash
bash scripts/test_docker_all.sh --cache-python /tmp/stts-python-cache --cache-nodejs /tmp/stts-nodejs-cache
```

## E2E examples

Poniżej są przykłady end-to-end, które da się uruchomić lokalnie oraz w CI.

### E2E offline (Docker, bez mikrofonu)

To jest najbardziej powtarzalne (deterministyczne):

- generujemy `samples/*.wav`
- zapisujemy oczekiwany tekst do `samples/*.wav.txt`
- ustawiamy `STTS_MOCK_STT=1` (STT czyta sidecar zamiast odpalać model)

```bash
make docker-test-python
make docker-test-nodejs
```

### E2E offline (placeholder / captions loop)

Tryb `--stt-stream-shell` pozwala odpalać w pętli komendę-szablon z podstawieniem `{STT}` / `{STT_STREAM}`.
W CI/Docker możesz to uruchomić jednorazowo z `--stt-file`:

```bash
STTS_MOCK_STT=1 ./stts --stt-file python/samples/cmd_echo_hello.wav \
  --stt-stream-shell --cmd "echo '{STT_STREAM}'" --dry-run
```

### E2E online (Deepgram, STT provider=deepgram)

Wersja Python ma provider `deepgram` (REST, transkrypcja z pliku WAV).

Wymaga:

- `STTS_DEEPGRAM_KEY=...`

Przykład (tylko transkrypcja):

```bash
STTS_DEEPGRAM_KEY=sk-... STTS_STT_PROVIDER=deepgram ./stts --stt-file python/samples/cmd_ls.wav --stt-only
```

Model można ustawić:

```bash
STTS_DEEPGRAM_KEY=sk-... STTS_STT_PROVIDER=deepgram STTS_DEEPGRAM_MODEL=nova-2 ./stts --stt-file python/samples/cmd_ls.wav --stt-only
```

## ✨ Funkcje

- **Auto-detekcja sprzętu** - sprawdza RAM, GPU, CPU i rekomenduje odpowiedni model
- **Wybór STT** - whisper.cpp, faster-whisper, vosk, Google Speech
- **Wybór TTS** - espeak, piper (neural), system TTS
- **Auto-pobieranie** - modele pobierane automatycznie
- **Cross-platform** - Linux, macOS, Windows, Raspberry Pi
- **Zero konfiguracji** - interaktywny setup przy pierwszym uruchomieniu
- **🎮 GPU Acceleration** - automatyczna kompilacja z CUDA (NVIDIA)
- **🔧 Text Normalization** - korekta błędów STT dla komend shell
- **⚡ Fast Start** - szybkie uruchamianie z lazy initialization

## 🎮 GPU Acceleration (CUDA)

Jeśli masz kartę NVIDIA z CUDA toolkit, whisper.cpp zostanie automatycznie skompilowany z GPU:

```bash
# Auto-detect (domyślne)
./stts --setup

# Wymuś GPU
STTS_GPU_ENABLED=1 ./stts --setup

# Wymuś CPU-only
STTS_GPU_ENABLED=0 ./stts --setup
```

Konfiguracja GPU layers (ile warstw modelu na GPU):

```bash
# Wszystkie warstwy na GPU (domyślne)
STTS_GPU_LAYERS=99 ./stts

# Tylko 20 warstw na GPU (hybrydowe)
STTS_GPU_LAYERS=20 ./stts
```

Wymagania:
- NVIDIA GPU z CUDA Compute Capability 5.0+
- CUDA Toolkit (`nvcc` w PATH)
- cmake

## 🔧 Text Normalization

STT może zwracać błędny tekst (literówki, źle rozpoznane komendy). `TextNormalizer` automatycznie poprawia typowe błędy:

| Błąd STT | Korekta |
|----------|---------|
| `el es`, `l s` | `ls` |
| `eko` | `echo` |
| `kopi`, `kopiuj` | `cp` |
| `git pusz` | `git push` |
| `pip instal` | `pip install` |
| `sudo apt instal` | `sudo apt install` |

Normalizacja jest automatyczna i nie wymaga konfiguracji.

## ⚡ Optymalizacja szybkości

Dla maksymalnej szybkości:

```bash
# Fast start (pomija wolną detekcję sprzętu)
STTS_FAST_START=1 ./stts

# Użyj mniejszego modelu
./stts --init whisper_cpp:tiny

# GPU + optymalne wątki (auto)
STTS_GPU_ENABLED=1 ./stts
```

Zmienne wydajnościowe:

| Zmienna | Opis | Domyślnie |
|---------|------|-----------|
| `STTS_GPU_ENABLED` | Wymusz GPU (1) lub CPU (0) | auto |
| `STTS_GPU_LAYERS` | Warstwy na GPU | 99 |
| `STTS_FAST_START` | Szybki start | 1 |
| `STTS_STREAM` | Strumieniuj output | 0 |

## 🚀 Instalacja

```bash
# 1. Pobierz
git clone https://github.com/wronai/stts
cd stts

# 2. Uruchom (wybierz wersję)
./stts           # Python 3.8+
./stts.mjs       # Node.js 18+

# 3. Opcjonalnie: zainstaluj globalnie
sudo ln -s $(pwd)/stts /usr/local/bin/stts
sudo ln -s $(pwd)/stts.mjs /usr/local/bin/stts-node
```

## 🔄 Python vs Node.js

| Cecha | Python (`python/stts`) | Node.js (`nodejs/stts.mjs`) |
|-------|-------------------------|----------------------------|
| Wymagania | Python 3.8+ | Node.js 18+ |
| Windows | ✅ Pełne | ⚠️ Częściowe |
| Linux/macOS | ✅ | ✅ |
| Zależności | 0 (stdlib) | 0 (stdlib) |

### Zależności systemowe

```bash
# Linux (Ubuntu/Debian)
sudo apt install espeak alsa-utils sox

# macOS
brew install espeak sox

# Windows
# Python + espeak (lub użyj system TTS)
```

## 📊 Wymagania sprzętowe

### STT (Speech-to-Text)

| Provider | Min RAM | GPU | Offline | Jakość | Szybkość |
|----------|---------|-----|---------|--------|----------|
| **whisper.cpp** | 1 GB | ❌ | ✅ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **faster-whisper** | 2 GB | ✅ (opt) | ✅ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **vosk** | 0.5 GB | ❌ | ✅ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **google** | 0.5 GB | ❌ | ❌ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

### Modele Whisper

| Model | RAM | VRAM | Rozmiar | Jakość |
|-------|-----|------|---------|--------|
| tiny | 1 GB | - | 75 MB | ⭐⭐ |
| base | 1 GB | - | 150 MB | ⭐⭐⭐ |
| small | 2 GB | - | 500 MB | ⭐⭐⭐⭐ |
| medium | 4 GB | 2 GB | 1.5 GB | ⭐⭐⭐⭐⭐ |
| large | 8 GB | 4 GB | 3 GB | ⭐⭐⭐⭐⭐ |

### TTS (Text-to-Speech)

| Provider | Min RAM | Jakość | Offline |
|----------|---------|--------|---------|
| **espeak** | 0.1 GB | ⭐⭐ | ✅ |
| **piper** | 0.5 GB | ⭐⭐⭐⭐⭐ | ✅ |
| **system** | - | ⭐⭐⭐ | ✅ |

## 💻 Użycie

### Voice Shell (interaktywny)

```bash
./stts

🔊 stts> make build       # wpisz komendę
🔊 stts>                  # ENTER = nagrywanie głosu
🔊 stts> exit             # wyjście
```

### Command Wrapper

```bash
# Uruchom komendę z głosowym output
./stts make build
./stts python script.py
./stts kubectl get pods
./stts git status

# Ostatnia linijka output zostanie przeczytana na głos
```

### STT placeholder (Python)

W trybie wrapper możesz użyć `{STT}` jako placeholdera, który zostanie zastąpiony transkryptem z mikrofonu:

```bash
STTS_NLP2CMD_ENABLED=1 ./stts nlp2cmd -r "{STT}"
```

### Pipeline (jednorazowe STT → stdout, Python)

Tryb `--stt-once` wypisuje sam transkrypt na stdout (a logi na stderr), więc nadaje się do pipe:

```bash
./stts --stt-once | xargs -I{} nlp2cmd -r "{}"
```

**Strumieniowanie komend z git:** Jeśli chcesz zobaczyć output `git` na bieżąco (bez bufora), użyj:

```bash
# Opcja 1: --dry-run + bash
./stts --dry-run git commit -m "{STT}" | bash

# Opcja 2: podstawienie argumentu (brak bufora)
git commit -m "$(./stts --stt-once)"
```

### Pipeline (TTS na końcu, Python)

Jeśli chcesz, żeby dowolny pipeline kończył się TTS (np. przeczytanie ostatniej niepustej linii), użyj:

```bash
... | ./stts --tts-stdin
```

Uwaga: `{TTS}` nie jest wbudowaną komendą – jeśli chcesz mieć skrót, ustaw alias w swoim shellu (np. `alias TTS='stts --tts-stdin'`).

Uwaga: aliasy (np. `TTS`) działają w Twoim shellu (bash/zsh), ale nie działają wewnątrz promptu `stts>`.

Przykład: zbuduj komendę i przeczytaj ją na głos (bez wykonania):

```bash
./stts --dry-run git commit -m "{STT}" | ./stts --tts-stdin
```

Jeśli koniecznie chcesz użyć aliasu, uruchom w normalnym shellu (nie w `stts>`), ewentualnie przez:

```bash
bash -c './stts --dry-run git commit -m "{STT}" | TTS'
```

### Makefile Integration

```makefile
# Dodaj do Makefile
%_voice:
	./stts make $*

# Użycie:
# make build_voice
# make test_voice
```

## ⚙️ Konfiguracja

```bash
# Interaktywny setup
./stts --setup

# Jednolinijkowy setup (Python)
./stts --init whisper_cpp:tiny

# TTS w jednej linijce (Python)
./stts --tts-provider espeak --tts-voice pl

# Konfiguracja zapisywana w:
~/.config/stts-python/config.json
```

### Przykładowa konfiguracja

```json
{
  "stt_provider": "whisper_cpp",
  "stt_model": "small",
  "tts_provider": "piper",
  "tts_voice": "pl",
  "language": "pl",
  "timeout": 5,
  "auto_tts": true
}
```

## 🔧 Providery

### STT: whisper.cpp (rekomendowany)

```bash
# Auto-instalacja przy setup
# Lub ręcznie:
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp && make
```

#### whisper.cpp + GPU (CUDA)

Jeśli masz CUDA toolkit (`nvcc`) i chcesz przyspieszyć transkrypcję na GPU:

```bash
# podczas instalacji (setup)
STTS_GPU_ENABLED=1 ./stts --setup

# przy uruchomieniu: offload warstw na GPU
./stts --stt-gpu-layers 35
# albo przez env:
STTS_STT_GPU_LAYERS=35 ./stts
```

### STT: faster-whisper (GPU)

```bash
pip install faster-whisper
```

### STT: vosk (lekki, RPi)

```bash
pip install vosk
```

### TTS: piper (neural, rekomendowany)

```bash
# Przykład (Python):
./stts --tts-provider piper --tts-voice pl_PL-gosia-medium

# albo podaj ścieżkę do modelu .onnx:
./stts --tts-provider piper --tts-voice ~/.config/stts-python/models/piper/pl_PL-gosia-medium.onnx

# Modele trzymane są w:
~/.config/stts-python/models/piper/
```

Wymagania:

- `piper` w `PATH` (binarka)
- model `*.onnx` w `~/.config/stts-python/models/piper/`
- odtwarzacz audio: `paplay` lub `aplay` lub `play`

Szybki check:

```bash
command -v piper
ls ~/.config/stts-python/models/piper/*.onnx
command -v paplay || command -v aplay || command -v play
```

**Automatyzacja (Python):**

```bash
# Auto-install piper + auto-download głosu
./stts --install-piper
./stts --download-piper-voice pl_PL-gosia-medium

# Lub przez Makefile
make tts-setup-piper
```

### TTS: espeak (fallback)

```bash
sudo apt install espeak
```

## 🍓 Raspberry Pi

Dla RPi rekomendowane:
- **STT**: vosk (small-pl) lub whisper.cpp (tiny)
- **TTS**: espeak lub piper

```bash
# RPi setup
sudo apt install espeak alsa-utils
./stts --setup
# Wybierz: vosk + espeak
```

## 🐛 Troubleshooting

### Brak mikrofonu

```bash
# Sprawdź
arecord -l

# Zainstaluj
sudo apt install alsa-utils
```

### Brak dźwięku TTS

```bash
# Diagnostyka (Python)
./stts --tts-test "Test TTS"

# Jeśli brak espeak/piper/player:
make tts-setup-espeak   # lub make tts-setup-piper
```

### Model nie pobiera się

```bash
# Ręczne pobranie whisper
wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin
mv ggml-small.bin ~/.config/stts/models/whisper.cpp/
```

## 📁 Struktura

```
stts/
├── python/
│   ├── stts
│   ├── README.md
│   ├── Makefile
│   ├── Dockerfile
│   ├── samples/
│   ├── scripts/
│   └── tests/
└── nodejs/
    ├── stts.mjs
    ├── README.md
    ├── Makefile
    ├── Dockerfile
    ├── samples/
    ├── scripts/
    └── tests/

~/.config/
├── stts-python/   # config + models dla Python
└── stts-nodejs/   # config + models dla Node.js
```

## 📚 Dokumentacja

- **Python**: `python/README.md` – szczegóły TTS, piper, VAD, audio, CLI
- **Node.js**: `nodejs/README.md` – szczegóły ESM, Docker, CLI
- **Docs**: `docs/README.md` – dodatkowe dokumenty (provider STT, testy E2E)
- **Examples**: `examples/README.md` – gotowe skrypty E2E do uruchomienia
- **.env**: `.env.example` (root) + `python/.env.example` + `nodejs/.env.example`
- **Makefile**: `python/Makefile` – targety `tts-setup-espeak`, `tts-setup-piper`

## 🔗 Powiązane projekty

### STT/TTS Engines
- **[whisper.cpp](https://github.com/ggerganov/whisper.cpp)** - High-performance inference of OpenAI's Whisper model
- **[faster-whisper](https://github.com/guillaumekint/faster-whisper)** - Faster Whisper transcription with CTranslate2
- **[vosk](https://github.com/alphacep/vosk-api)** - Offline speech recognition API
- **[piper](https://github.com/rhasspy/piper)** - Fast, local neural text-to-speech system
- **[espeak](https://espeak.sourceforge.io/)** - Compact open source speech synthesizer

### CLI Tools
- **[nlp2cmd](https://github.com/wronai/nlp2cmd)** - Natural Language to Command converter
- **[whisper-cli](https://github.com/ahmedkheir/whisper-cli)** - Command-line interface for Whisper

### Audio Libraries
- **[pyaudio](https://github.com/pyaudio/pyaudio)** - Python bindings for PortAudio
- **[sox](https://sox.sourceforge.io/)** - Sound eXchange - universal sound processing utility

## 📜 Licencja

Apache 2.0
