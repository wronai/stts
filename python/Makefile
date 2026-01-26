.PHONY: setup voice test-tts gen-samples docker-build docker-test help \
	stt-vosk-pl stt-silero stt-whisper-stream \
	tts-piper-pl tts-mimic3 tts-festival \
	setup-local-full test-local

CACHE_DIR ?= $(HOME)/.config/stts-python
DOCKER_RUN_USER ?= $(shell id -u):$(shell id -g)

# Use venv if available, otherwise system python
VENV_DIR ?= $(shell pwd)/../venv
ifeq ($(wildcard $(VENV_DIR)/bin/pip),)
  PIP := python3 -m pip install --user
else
  PIP := $(VENV_DIR)/bin/pip install
endif

setup:
	@./stts --setup

voice:
	@./stts

test-tts:
	@command -v espeak >/dev/null && espeak -v pl "Test syntezatora mowy" || echo "❌ espeak not found"

# TTS automation (Linux)
tts-setup-espeak:
	@echo "Install (Linux): sudo apt install -y espeak pulseaudio-utils alsa-utils"
	@./stts --tts-provider espeak --tts-voice pl
	@./stts --tts-test "Test syntezatora mowy (espeak)"

tts-setup-piper:
	@./stts --tts-provider piper --tts-voice pl_PL-gosia-medium
	@./stts --install-piper
	@./stts --download-piper-voice pl_PL-gosia-medium
	@./stts --tts-test "Test syntezatora mowy (piper)"

gen-samples:
	@./scripts/generate_samples.sh

docker-build:
	@docker build -t stts-python:latest .

docker-test:
	@docker build -t stts-python:latest .
	@mkdir -p $(CACHE_DIR)
	@docker run --rm -t \
		--user $(DOCKER_RUN_USER) \
		-e STTS_CONFIG_DIR=/stts-cache \
		-v $(CACHE_DIR):/stts-cache \
		stts-python:latest ./tests/docker_test.sh

# Run interactively with cache mounted from host
# Usage:
#   make docker-run CACHE_DIR=~/.config/stts-python
docker-run:
	@docker build -t stts-python:latest .
	@docker run --rm -it \
		-e STTS_CONFIG_DIR=/stts-cache \
		-v $(CACHE_DIR):/stts-cache \
		stts-python:latest ./stts

help:
	@echo "stts (python)"
	@echo ""
	@echo "Basic:"
	@echo "  make setup            - setup wizard"
	@echo "  make voice            - interactive voice shell"
	@echo "  make gen-samples      - generate WAV samples"
	@echo "  make docker-test      - run tests in docker (no mic)"
	@echo ""
	@echo "Local STT (offline):"
	@echo "  make stt-vosk-pl      - install Vosk + Polish model (50MB, fast)"
	@echo "  make stt-silero       - install Silero STT (torch-based)"
	@echo "  make stt-whisper-stream - build whisper.cpp streaming mode"
	@echo ""
	@echo "Local TTS (offline):"
	@echo "  make tts-setup-espeak - configure espeak TTS"
	@echo "  make tts-setup-piper  - configure piper TTS (auto-download)"
	@echo "  make tts-piper-pl     - install Piper + Polish voices"
	@echo "  make tts-mimic3       - install Mimic3 TTS"
	@echo "  make tts-festival     - install Festival TTS"
	@echo ""
	@echo "Full local stack:"
	@echo "  make setup-local-full - install Vosk PL + Piper PL (250MB)"
	@echo "  make test-local       - test local STT+TTS pipeline"
	@echo ""
	@echo "Extras:"
	@echo "  make pip-nlp2cmd      - install nlp2cmd"
	@echo "  make pip-extras       - install optional libs"

pip-nlp2cmd:
	@echo "Installing nlp2cmd..."
	@python3 -m pip install -U nlp2cmd

pip-extras:
	@echo "Installing optional libraries..."
	@python3 -m pip install -U pexpect SpeechRecognition pyaudio playwright pyautogui

# ============================================================================
# LOCAL STT PROVIDERS (offline, no API)
# ============================================================================

# Vosk: fast (~300ms), small model, good PL support
stt-vosk-pl:
	@echo "📦 Installing Vosk + Polish model..."
	@$(PIP) -U vosk
	@mkdir -p $(CACHE_DIR)/models/vosk
	@echo "📥 Downloading vosk-model-small-pl-0.22..."
	@rm -f /tmp/vosk-small-pl.zip
	@curl -L -o /tmp/vosk-small-pl.zip \
		"https://alphacephei.com/vosk/models/vosk-model-small-pl-0.22.zip"
	@cd $(CACHE_DIR)/models/vosk && unzip -o /tmp/vosk-small-pl.zip
	@rm -f /tmp/vosk-small-pl.zip
	@echo "✅ Vosk PL ready: $(CACHE_DIR)/models/vosk/vosk-model-small-pl-0.22"

# Silero STT: fast CPU inference, good PL/EN
stt-silero:
	@echo "📦 Installing Silero STT..."
	@$(PIP) -U torch torchaudio
	@echo "✅ Silero STT ready (models downloaded on first use)"

# Whisper.cpp streaming mode
stt-whisper-stream:
	@echo "🔧 Building whisper.cpp stream..."
	@cd $(CACHE_DIR)/models/whisper.cpp && make stream
	@echo "✅ whisper.cpp stream ready"

# ============================================================================
# LOCAL TTS PROVIDERS (offline, no API)
# ============================================================================

# Piper PL voices (best quality, neural)
tts-piper-pl:
	@echo "📦 Installing Piper + Polish voices..."
	@./stts --install-piper
	@./stts --download-piper-voice pl_PL-gosia-medium
	@./stts --download-piper-voice pl_PL-darkman-medium || true
	@echo "✅ Piper PL voices ready"

# Mimic3 (Mycroft successor, 100% offline)
tts-mimic3:
	@echo "📦 Installing Mimic3..."
	@$(PIP) -U mycroft-mimic3-tts
	@echo "✅ Mimic3 ready. Test: mimic3 --voice pl_PL/m-ailabs_low 'Test'"

# Festival (lightweight PL)
tts-festival:
	@echo "📦 Installing Festival..."
	@echo "Run: sudo apt install -y festival festvox-kallpc16k"
	@echo "✅ Festival ready (if installed)"

# ============================================================================
# FULL LOCAL SETUP (zero network after install)
# ============================================================================

setup-local-full: stt-vosk-pl tts-piper-pl
	@echo ""
	@echo "🎉 Full local STT+TTS stack installed!"
	@echo ""
	@echo "Add to .env:"
	@echo "  STTS_STT_PROVIDER=vosk"
	@echo "  STTS_STT_MODEL=small-pl"
	@echo "  STTS_TTS_PROVIDER=piper"
	@echo "  STTS_TTS_VOICE=pl_PL-gosia-medium"
	@echo ""
	@echo "Test: make test-local"

# Test local pipeline (STT -> TTS)
test-local:
	@echo "🧪 Testing local STT+TTS pipeline..."
	@./stts --tts-test "Test lokalnego syntezatora mowy"
	@echo "✅ TTS OK"
	@echo ""
	@echo "To test STT, run: ./stts --stt-file samples/cmd_echo_hello.wav --stt-only"
