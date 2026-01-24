.PHONY: setup voice test-tts gen-samples docker-build docker-test help

CACHE_DIR ?= $(HOME)/.config/stts-python
DOCKER_RUN_USER ?= $(shell id -u):$(shell id -g)

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
	@echo "  make setup         - setup wizard"
	@echo "  make voice         - interactive voice shell"
	@echo "  make gen-samples   - generate WAV samples"
	@echo "  make tts-setup-espeak - configure and test espeak TTS"
	@echo "  make tts-setup-piper  - configure and test piper TTS (auto-download)"
	@echo "  make pip-nlp2cmd   - install nlp2cmd (example NLP interface)"
	@echo "  make pip-extras    - install optional voice/automation libs (examples)"
	@echo "  make docker-test   - run tests in docker (no mic)"

pip-nlp2cmd:
	@echo "Installing nlp2cmd..."
	@python3 -m pip install -U nlp2cmd

pip-extras:
	@echo "Installing optional libraries..."
	@python3 -m pip install -U pexpect SpeechRecognition pyaudio playwright pyautogui
