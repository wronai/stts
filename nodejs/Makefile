.PHONY: setup voice gen-samples docker-build docker-test help

setup:
	@./stts.mjs --setup

voice:
	@./stts.mjs

gen-samples:
	@./scripts/generate_samples.sh

docker-build:
	@docker build -t stts-nodejs:latest .

docker-test:
	@docker build -t stts-nodejs:latest .
	@docker run --rm -t stts-nodejs:latest ./tests/docker_test.sh

help:
	@echo "stts (nodejs)"
	@echo "  make setup         - setup wizard"
	@echo "  make voice         - interactive voice shell"
	@echo "  make gen-samples   - generate WAV samples"
	@echo "  make docker-test   - run tests in docker (no mic)"
