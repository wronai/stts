# STT Providers

## Implemented

| Provider | Type | Best For | Install |
|----------|------|----------|---------|
| `whisper_cpp` | Offline | Docker/CI, local | auto-build |
| `deepgram` | Online | Production, accuracy | API key |
| `vosk` | Offline | RPi, embedded, low-latency | `make stt-vosk-pl` |
| `faster_whisper` | Offline | GPU/CPU, high quality | `pip install faster-whisper` |
| `coqui` | Offline | Custom models | `pip install coqui-stt` |
| `picovoice` | Offline | Wake-word + STT | API key |

---

### whisper.cpp (`stt_provider=whisper_cpp`)

- **Type:** Offline
- **Best for:** Docker/CI and local usage
- **Models:** `~/.config/stts-python/models/whisper.cpp/`
- **GPU:** Set `STTS_GPU_ENABLED=1` and `STTS_STT_GPU_LAYERS=32` for CUDA

```bash
STTS_STT_PROVIDER=whisper_cpp STTS_STT_MODEL=base ./stts --stt-file audio.wav --stt-only
```

### faster-whisper (`stt_provider=faster_whisper`)

- **Type:** Offline
- **Best for:** High accuracy + good speed (CTranslate2), GPU optional
- **Package:** `pip install faster-whisper`
- **Tuning:**
  - `STTS_FASTER_WHISPER_DEVICE=auto|cpu|cuda`
  - `STTS_FASTER_WHISPER_COMPUTE_TYPE=int8|float16|float32`

```bash
STTS_STT_PROVIDER=faster_whisper STTS_STT_MODEL=base ./stts --stt-file audio.wav --stt-only
```

### Deepgram (`stt_provider=deepgram`)

- **Type:** Online (REST)
- **Requires:** `STTS_DEEPGRAM_KEY`
- **Model:** `STTS_DEEPGRAM_MODEL` (default `nova-2`)

```bash
STTS_DEEPGRAM_KEY=sk-... STTS_STT_PROVIDER=deepgram ./stts --stt-file audio.wav --stt-only
```

### Vosk (`stt_provider=vosk`)

- **Type:** Offline
- **Best for:** RPi, embedded, ultra-low-latency (<200ms)
- **Models:** `~/.config/stts-python/models/vosk/`
- **Languages:** pl, en, af, de, fr, es, ru, ...

```bash
# Install Polish model
make stt-vosk-pl

# Use
STTS_STT_PROVIDER=vosk STTS_STT_MODEL=small-pl ./stts --stt-file audio.wav --stt-only
```

**Code snippet:**
```python
import vosk
from vosk import KaldiRecognizer
model = vosk.Model("vosk-model-small-pl-0.22")
rec = KaldiRecognizer(model, 16000)
rec.AcceptWaveform(audio_bytes)
text = rec.FinalResult()
```

### Coqui STT (`stt_provider=coqui`)

- **Type:** Offline
- **Package:** `pip install coqui-stt`
- **Models:** Custom .tflite or .pbmm

```bash
STTS_STT_PROVIDER=coqui STTS_STT_MODEL=/path/to/model.tflite ./stts --stt-file audio.wav --stt-only
```

### Picovoice (`stt_provider=picovoice`)

- **Type:** Offline (wake-word + STT)
- **Requires:** `PICOVOICE_ACCESS_KEY`
- **Best for:** Always-on wake-word detection

---

## Optional / roadmap (not yet implemented)

### DeepSpeech

- **Package:** `pip install deepspeech`
- **Docker:** `docker run -it mozilla/deepspeech`
- **Status:** Legacy (Mozilla discontinued), use Coqui STT instead

```python
import deepspeech
model = deepspeech.Model("deepspeech-0.9.3-models.pbmm")
text = model.stt(audio_buffer)
```

### April-ASR

- **Package:** `pip install april-asr`
- **Type:** Offline, streaming-capable
- **Best for:** Low-resource embedded

```python
from april_asr import AprilASR
asr = AprilASR(model_path="/path/to/model")
text = asr.decode(audio_samples)
```

### whisper.cpp streaming

- Binary: `stream` (part of whisper.cpp build)
- Would require parsing partial output from stdout

---

## Multi-engine Docker Stack

```yaml
# docker-compose.yml
services:
  stt-whisper:
    image: lintoai/linto-stt-whisper
    environment:
      - MODEL=deepdml/faster-whisper-large-v3-turbo-ct2
  stt-vosk:
    image: rhasspy/wyoming-vosk
    volumes: ['./models:/data']
  ovos-stt:
    image: smartgic/ovos-stt-server-fasterwhisper
```

## Language Support

| Provider | Polish | English | Afrikaans | Notes |
|----------|--------|---------|-----------|-------|
| whisper.cpp | ✅ | ✅ | ✅ | `language="af"` |
| Vosk | ✅ | ✅ | ❌ | Download model per language |
| Deepgram | ✅ | ✅ | ✅ | `language` param |
| faster-whisper | ✅ | ✅ | ✅ | `language="af"` |
