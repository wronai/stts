.PHONY: setup voice test-tts gen-samples docker-build docker-test help

CACHE_DIR ?= $(HOME)/.config/stts-python

setup:
	@./stts --setup

voice:
	@./stts

test-tts:
	@command -v espeak >/dev/null && espeak -v pl "Test syntezatora mowy" || echo "❌ espeak not found"

gen-samples:
	@./scripts/generate_samples.sh

docker-build:
	@docker build -t stts-python:latest .

docker-test:
	@docker build -t stts-python:latest .
	@docker run --rm -t stts-python:latest ./tests/docker_test.sh

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
	@echo "  make docker-test   - run tests in docker (no mic)"
