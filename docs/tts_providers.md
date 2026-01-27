# TTS Providers

## Implemented

| Provider | Type | Quality | Best For | Install |
|----------|------|---------|----------|---------|
| espeak | Offline | Basic | Fallback, lightweight | `apt install espeak-ng` |
| piper | Offline | High | Production, multilingual | auto-download |
| rhvoice | Offline | Medium | Slavic languages | `apt install rhvoice` |
| coqui-tts | Offline | High | Neural voices, multilingual | `pip install TTS` |
| kokoro | Offline | High | Fast CPU neural | `pip install kokoro scipy` |
| festival | Offline | Basic | Ultra-lightweight | `apt install festival` |
| flite | Offline | Basic | Embedded | `apt install flite` |
| spd-say | Offline | Varies | Speech-dispatcher | `apt install speech-dispatcher` |
| say | Offline | High | macOS only | built-in |

---

## Implemented Providers

### eSpeak (`tts_provider=espeak`)

- **Type:** Offline, formant synthesis
- **Quality:** Basic (robotic)
- **Best for:** Fallback, lightweight, Afrikaans support

```bash
# Install
apt install espeak-ng

# Use
STTS_TTS_PROVIDER=espeak STTS_TTS_VOICE=pl ./stts
```

**Afrikaans:**
```bash
espeak-ng -v af "Hallo wêreld" -w out.wav
```

### Piper (`tts_provider=piper`)

- **Type:** Offline, neural (VITS)
- **Quality:** High
- **Best for:** Production, multilingual, RPi-compatible
- **Models:** Auto-downloaded to `~/.config/stts-python/models/piper/`

```bash
STTS_TTS_PROVIDER=piper STTS_TTS_VOICE=pl_PL-gosia-medium ./stts
```

**Code snippet:**
```python
# pip install piper-tts
from piper import PiperVoice
voice = PiperVoice.load("pl_PL-gosia-medium.onnx")
audio = voice.synthesize("Cześć!")
```

**Docker:**
```bash
docker run -p 10200:10200 rhasspy/piper --voice pl_PL-gosia-medium
```

### RHVoice (`tts_provider=rhvoice`)

- **Type:** Offline, parametric
- **Quality:** Medium-High
- **Best for:** Polish, Russian, Ukrainian, Georgian

```bash
# Install
apt install rhvoice rhvoice-polish

# Use
STTS_TTS_PROVIDER=rhvoice STTS_TTS_VOICE=Anna ./stts
```

**Code snippet:**
```bash
rhvoice-speak -l pl "Tekst do przeczytania"
```

**Docker:**
```bash
docker run -p 8080:8080 ovos/rhvoice-wrapper
```

### Coqui TTS (`tts_provider=coqui-tts`)

- **Type:** Offline, neural (Tacotron2, VITS, XTTS)
- **Quality:** High
- **Best for:** Neural voices, voice cloning (XTTS)

```bash
# Install
pip install TTS

# Use
STTS_TTS_PROVIDER=coqui-tts STTS_COQUI_TTS_MODEL=tts_models/pl/mai/tacotron2-DDC ./stts
```

**Code snippet:**
```python
from TTS.api import TTS
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
tts.tts_to_file("Tekst", file_path="out.wav", language="pl")
```

**Voice cloning (XTTS):**
```python
tts.tts_to_file(
    "Tekst do przeczytania",
    speaker_wav="reference_voice.wav",
    language="pl",
    file_path="cloned.wav"
)
```

### Kokoro (`tts_provider=kokoro`)

- **Type:** Offline, neural
- **Quality:** High
- **Best for:** Low-latency, streaming

```bash
STTS_TTS_PROVIDER=kokoro STTS_TTS_VOICE=pl ./stts
```

### Festival (`tts_provider=festival`)

- **Type:** Offline, unit selection
- **Quality:** Basic
- **Best for:** Ultra-lightweight, no dependencies

```bash
apt install festival festvox-kallpc16k
STTS_TTS_PROVIDER=festival ./stts
```

### Flite (`tts_provider=flite`)

- **Type:** Offline, tiny footprint
- **Quality:** Basic
- **Best for:** Embedded, minimal resources

```bash
apt install flite
STTS_TTS_PROVIDER=flite ./stts
```

---

## Roadmap (not yet implemented)

### Mimic3

- **Package:** `pip install mycroft-mimic3-tts`
- **Docker:** `docker run mycroftai/mimic3`
- **Quality:** High (neural VITS)

```python
# pip install mycroft-mimic3-tts
import subprocess
subprocess.run(["mimic3", "--voice", "pl_PL/gosia_low", "Tekst"], stdout=open("out.wav", "wb"))
```

### MBROLA

- **Type:** Offline, diphone
- **Best for:** Research, specific phoneme control

```bash
apt install mbrola mbrola-pl1
echo "Tekst" | espeak-ng -v mb-pl1 -w out.wav
```

### F5-TTS

- **Package:** `pip install f5-tts`
- **Type:** Zero-shot voice cloning

```python
from f5_tts import F5TTS
f5 = F5TTS()
f5.generate("Tekst", ref_audio="reference.wav", output="out.wav")
```

### Parler-TTS

- **Package:** `pip install parler-tts`
- **Type:** Prompted TTS (describe voice characteristics)

```python
from parler_tts import ParlerTTS
tts = ParlerTTS.from_pretrained("parler-tts/parler_tts_mini_v0.1")
audio = tts.generate(
    "Hello world",
    description="A female speaker with a soft voice, speaking slowly"
)
```

### WhisperSpeech (XTTS alternative)

- **Type:** Whisper-based TTS
- **Best for:** Multilingual voice cloning

```python
# Part of Coqui TTS
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
```

### S.A.M. (Software Automatic Mouth)

- **Package:** `pip install sam-tts`
- **Type:** Retro 8-bit synth
- **Best for:** Nostalgic/creative projects

```python
from sam import SAM
sam = SAM()
sam.say("Hello world")
```

---

## Multi-engine Docker Stack

```yaml
# docker-compose.yml
services:
  tts-piper:
    image: rhasspy/piper
    ports: ["10200:10200"]
    volumes: ['./voices:/voices']
    command: --voice pl_PL-gosia-medium
    
  tts-coqui:
    image: coqui-ai/tts-cpu
    ports: ["5002:5002"]
    environment:
      - MODEL=tts_models/multilingual/multi-dataset/xtts_v2
      
  tts-rhvoice:
    image: ovos/rhvoice-wrapper
    ports: ["8080:8080"]
```

## Language Support

| Provider | Polish | English | Afrikaans | Notes |
|----------|--------|---------|-----------|-------|
| eSpeak | ✅ | ✅ | ✅ | `-v af` |
| Piper | ✅ | ✅ | ⚠️ | Check model availability |
| RHVoice | ✅ | ✅ | ❌ | Strong Slavic support |
| Coqui TTS | ✅ | ✅ | ✅ | XTTS multilingual |
| Kokoro | ✅ | ✅ | ⚠️ | Model dependent |

## Performance Comparison

| Provider | Latency | RAM | Quality | Streaming |
|----------|---------|-----|---------|-----------|
| eSpeak | <50ms | <10MB | ⭐⭐ | ✅ |
| Piper | ~200ms | ~500MB | ⭐⭐⭐⭐ | ✅ |
| Coqui XTTS | ~1-3s | ~2GB | ⭐⭐⭐⭐⭐ | ❌ |
| Kokoro | ~100ms | ~1GB | ⭐⭐⭐⭐ | ✅ |
| RHVoice | ~100ms | ~200MB | ⭐⭐⭐ | ✅ |

---

## Bergamot MT Integration

For multilingual TTS with translation, run a translator *before* passing text to TTS (external to `stts`).

**Docker:**
```yaml
services:
  bergamot:
    image: browsermt/bergamot-translator
    ports: ["8787:8787"]
```

**Use case:** Translate English input → Polish text → Piper TTS
