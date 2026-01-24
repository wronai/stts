# 🎙️ stts - Universal Voice Shell

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
# z konfiguracją TTS
./stts git commit -m "{STT}" | ./stts --tts-provider piper --tts-voice pl_PL-gosia-medium --tts-stdin
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

## NLP2CMD (Natural Language → komendy)

W wersji Python i Node możesz:

- wpisać: `nlp Pokaż użytkowników`
- albo użyć STT: ENTER → powiedz tekst → skrypt odpali `nlp2cmd` i zapyta o potwierdzenie

Instalacja `nlp2cmd`:

```bash
cd python && make pip-nlp2cmd
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

## ✨ Funkcje

- **Auto-detekcja sprzętu** - sprawdza RAM, GPU, CPU i rekomenduje odpowiedni model
- **Wybór STT** - whisper.cpp, faster-whisper, vosk, Google Speech
- **Wybór TTS** - espeak, piper (neural), system TTS
- **Auto-pobieranie** - modele pobierane automatycznie
- **Cross-platform** - Linux, macOS, Windows, Raspberry Pi
- **Zero konfiguracji** - interaktywny setup przy pierwszym uruchomieniu

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
bash -lc './stts --dry-run git commit -m "{STT}" | TTS'
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
# Test espeak
espeak "test"

# Zainstaluj
sudo apt install espeak
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

## 📜 Licencja

Apache 2.0
