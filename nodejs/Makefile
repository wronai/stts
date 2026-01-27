.PHONY: setup voice test gen-samples docker-build docker-test help

CACHE_DIR ?= $(HOME)/.config/stts-nodejs

setup:
	@./stts.mjs --setup

voice:
	@./stts.mjs

test:
	@if command -v node >/dev/null 2>&1; then \
		echo "🧪 Running Node.js CLI smoke tests (mock STT)..."; \
		STTS_SKIP_SAMPLE_GEN=$${STTS_SKIP_SAMPLE_GEN:-1} bash tests/docker_test.sh; \
	else \
		echo "⏭  Skipping Node.js tests (node not found)"; \
	fi

gen-samples:
	@./scripts/generate_samples.sh

docker-build:
	@docker build -t stts-nodejs:latest .

docker-test:
	@docker build -t stts-nodejs:latest .
	@docker run --rm -t stts-nodejs:latest ./tests/docker_test.sh

# Run interactively with cache mounted from host
# Usage:
#   make docker-run CACHE_DIR=~/.config/stts-nodejs
docker-run:
	@docker build -t stts-nodejs:latest .
	@docker run --rm -it \
		-e STTS_CONFIG_DIR=/stts-cache \
		-v $(CACHE_DIR):/stts-cache \
		stts-nodejs:latest node ./stts.mjs

help:
	@echo "stts (nodejs)"
	@echo "  make setup         - setup wizard"
	@echo "  make voice         - interactive voice shell"
	@echo "  make test          - run CLI smoke tests (mock STT)"
	@echo "  make gen-samples   - generate WAV samples"
	@echo "  make pip-nlp2cmd   - install nlp2cmd (used for NL -> cmd)"
	@echo "  make docker-test   - run tests in docker (no mic)"

pip-nlp2cmd:
	@echo "Installing nlp2cmd (python package)..."
	@python3 -m pip install -U nlp2cmd
