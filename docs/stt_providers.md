# STT Providers

## Implemented

| Provider | Type | Best For | Install |
|----------|------|----------|---------|
| whisper.cpp | Offline | Docker/CI, local | auto-build |
| Deepgram | Online | Production, accuracy | API key |
| Vosk | Offline | RPi, embedded, low-latency | `make stt-vosk-pl` |
| Coqui STT | Offline | Custom models | `pip install stt` |
| Picovoice | Offline | Wake-word + STT | API key |

---

### whisper.cpp (`stt_provider=whisper_cpp`)

- **Type:** Offline
- **Best for:** Docker/CI and local usage
- **Models:** `~/.config/stts-python/models/whisper.cpp/`
- **GPU:** Set `STTS_GPU_ENABLED=1` and `STTS_STT_GPU_LAYERS=32` for CUDA

```bash
STTS_STT_PROVIDER=whisper_cpp STTS_STT_MODEL=base ./stts --stt-file audio.wav --stt-only
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
- **Package:** `pip install stt`
- **Models:** Custom .tflite or .pbmm

```bash
STTS_STT_PROVIDER=coqui STTS_COQUI_MODEL=/path/to/model.tflite ./stts --stt-file audio.wav --stt-only
```

### Picovoice (`stt_provider=picovoice`)

- **Type:** Offline (wake-word + STT)
- **Requires:** `STTS_PICOVOICE_KEY`
- **Best for:** Always-on wake-word detection

---

## Roadmap (not yet implemented)

### DeepSpeech

- **Package:** `pip install deepspeech`
- **Docker:** `docker run -it mozilla/deepspeech`
- **Status:** Legacy (Mozilla discontinued), use Coqui STT instead

```python
import deepspeech
model = deepspeech.Model("deepspeech-0.9.3-models.pbmm")
text = model.stt(audio_buffer)
```

### faster-whisper / Distil-Whisper

- **Package:** `pip install faster-whisper`
- **Docker:** `docker run lintoai/linto-stt-whisper`
- **Models:** `distil-large-v3` (GPU), `tiny`/`base` (CPU/RPi)
- **Best for:** Real-time streaming with `compute_type="int8"`

```python
from faster_whisper import WhisperModel
model = WhisperModel("base", compute_type="int8")
segments, _ = model.transcribe("audio.wav", language="pl")
text = " ".join(seg.text for seg in segments)
```

**Suggested integration:**
- Add `stt_provider=faster_whisper`
- Streaming mode: 100–200ms chunks with partial captions

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
