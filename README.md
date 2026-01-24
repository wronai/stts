# 🎙️ stts - Universal Voice Shell

**STT + TTS shell wrapper** - uruchamiaj dowolne komendy głosem!

```bash
# Python version
./stts                    # Voice shell
./stts make build         # Komenda z głosowym output
./stts --setup            # Konfiguracja

# Node.js version (alternatywa)
./stts.mjs                # Voice shell
./stts.mjs make build     # Komenda z głosowym output
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

| Cecha | Python (`stts`) | Node.js (`stts.mjs`) |
|-------|-----------------|----------------------|
| Wymagania | Python 3.8+ | Node.js 18+ |
| Windows | ✅ Pełne | ⚠️ Częściowe |
| Linux/macOS | ✅ | ✅ |
| Rozmiar | 25 KB | 20 KB |
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

# Konfiguracja zapisywana w:
~/.config/stts/config.json
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
# Auto-pobieranie przy setup
# Głosy: pl_PL-gosia-medium, en_US-lessac-medium
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
├── stts                 # Python version
├── stts.mjs             # Node.js version
├── Makefile             # Make integration
└── README.md

~/.config/stts/
├── config.json          # Konfiguracja (wspólna)
├── history              # Historia komend
└── models/
    ├── whisper.cpp/     # Modele whisper
    │   ├── main         # Binary
    │   └── ggml-*.bin   # Modele
    ├── piper/           # Piper TTS
    │   └── voices/      # Głosy
    └── vosk/            # Modele vosk
```

## 📜 Licencja

MIT
