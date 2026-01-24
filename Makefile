# stts - Universal Voice Shell
# Makefile integration

.PHONY: install test voice setup clean help setup-python setup-nodejs voice-python voice-nodejs gen-samples-python gen-samples-nodejs docker-build-python docker-build-nodejs docker-test-python docker-test-nodejs

VERSION := $(shell cat VERSION 2>/dev/null || echo 0.0.0)

# Install stts globally (both versions)
install:
	@echo "Installing stts..."
	@chmod +x python/stts nodejs/stts.mjs
	@sudo ln -sf $(shell pwd)/python/stts /usr/local/bin/stts
	@sudo ln -sf $(shell pwd)/nodejs/stts.mjs /usr/local/bin/stts-node
	@echo "✅ Installed! Run: stts (Python) or stts-node (Node.js)"

# Install dependencies (Linux)
deps:
	@echo "📦 Installing dependencies..."
	@sudo apt install -y espeak alsa-utils sox python3
	@echo "✅ Dependencies installed!"

# Run setup wizard
setup:
	@./stts --setup

setup-node:
	@./stts.mjs --setup

# Start voice shell
voice:
	@./stts

voice-node:
	@./stts.mjs

# Delegation targets for split projects
setup-python:
	@$(MAKE) -C python setup

setup-nodejs:
	@$(MAKE) -C nodejs setup

voice-python:
	@$(MAKE) -C python voice

voice-nodejs:
	@$(MAKE) -C nodejs voice

gen-samples-python:
	@$(MAKE) -C python gen-samples

gen-samples-nodejs:
	@$(MAKE) -C nodejs gen-samples

docker-build-python:
	@$(MAKE) -C python docker-build

docker-build-nodejs:
	@$(MAKE) -C nodejs docker-build

docker-test-python:
	@$(MAKE) -C python docker-test

docker-test-nodejs:
	@$(MAKE) -C nodejs docker-test

# Test TTS
test-tts:
	@echo "🔊 Testing TTS..."
	@command -v espeak >/dev/null && espeak -v pl "Test syntezatora mowy" || echo "❌ espeak not found"

# Test STT (record 3s)
test-stt:
	@echo "🎤 Testing microphone (3s)..."
	@arecord -d 3 -f cd -t wav /tmp/test.wav && echo "✅ Recorded to /tmp/test.wav" || echo "❌ Recording failed"

# Clean models and config
clean:
	@echo "🧹 Cleaning..."
	@rm -rf ~/.config/stts/models
	@echo "✅ Models removed. Config preserved."

# Full clean (including config)
clean-all:
	@echo "🧹 Full clean..."
	@rm -rf ~/.config/stts
	@echo "✅ All stts data removed."

# Voice wrapper for any make target (Python)
%_voice:
	@./stts make $*

# Voice wrapper for any make target (Node.js)
%_voice_node:
	@./stts.mjs make $*

# Help
help:
	@echo "stts - Universal Voice Shell"
	@echo ""
	@echo "Targets:"
	@echo "  make install      - Install stts globally (Python + Node.js)"
	@echo "  make deps         - Install system dependencies (Linux)"
	@echo "  make setup        - Run setup wizard (Python)"
	@echo "  make setup-node   - Run setup wizard (Node.js)"
	@echo "  make version      - Show current version"
	@echo "  make bump-patch   - Bump patch version (x.y.z -> x.y.z+1)"
	@echo "  make bump-minor   - Bump minor version (x.y.z -> x.y+1.0)"
	@echo "  make bump-major   - Bump major version (x.y.z -> x+1.0.0)"
	@echo "  make publish-npm  - Publish to npmjs (uses current version)"
	@echo "  make publish-pypi - Publish to PyPI (uses current version)"
	@echo "  make publish      - Publish to both npmjs and PyPI"
	@echo "  make voice        - Start voice shell (Python)"
	@echo "  make voice-node   - Start voice shell (Node.js)"
	@echo "  make test-tts     - Test TTS"
	@echo "  make test-stt     - Test microphone"
	@echo "  make clean        - Remove downloaded models"
	@echo "  make clean-all    - Remove all stts data"
	@echo ""
	@echo "Voice wrapper:"
	@echo "  make TARGET_voice       - Run 'make TARGET' with voice (Python)"
	@echo "  make TARGET_voice_node  - Run 'make TARGET' with voice (Node.js)"
	@echo "  Example: make build_voice"

version:
	@echo $(VERSION)

bump-patch:
	@python3 bump_version.py patch

bump-minor:
	@python3 bump_version.py minor

bump-major:
	@python3 bump_version.py major

publish-npm:
	@npm publish

publish-pypi:
	@python3 -m build
	@python3 -m twine upload dist/*

publish: publish-npm publish-pypi
