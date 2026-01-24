.PHONY: setup voice test-tts gen-samples docker-build docker-test help

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

help:
	@echo "stts (python)"
	@echo "  make setup         - setup wizard"
	@echo "  make voice         - interactive voice shell"
	@echo "  make gen-samples   - generate WAV samples"
	@echo "  make docker-test   - run tests in docker (no mic)"
