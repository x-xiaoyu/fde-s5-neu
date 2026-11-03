.PHONY: install env ollama models serve check

# Own machine, once:   make install   (then: conda activate fde-s5)
# Codespace, once:     make models    (.devcontainer installs Ollama and the packages)
# Check it works:      make check
# Every time:          make serve     (own machine: conda activate fde-s5 first)

# Mac: the app lives in the conda env (nothing in /Applications or /usr/local/bin);
# conda env remove -n fde-s5 removes it
ifeq ($(shell uname -s),Darwin)
APP := $(shell conda info --base)/envs/fde-s5/Ollama.app
OLLAMA = $(APP)/Contents/Resources/ollama
else
OLLAMA = ollama
endif

install: env ollama models

env:
	conda env create -f environment.yml || conda env update -f environment.yml --prune

# Mac: Ollama's signed app, checked before it goes in the env. Linux: Ollama's install script.
ollama:
ifeq ($(shell uname -s),Darwin)
	test -d $(APP) || { set -e; t=$$(mktemp -d); \
	  curl -fsSL -o $$t/o.zip https://ollama.com/download/Ollama-darwin.zip && unzip -q $$t/o.zip -d $$t; \
	  codesign --verify --deep --strict $$t/Ollama.app && spctl -a -t exec -v $$t/Ollama.app; \
	  mv $$t/Ollama.app $(APP); }
	ln -sf $(OLLAMA) $(dir $(APP))bin/ollama   # so ollama works with the env active
else
	command -v ollama || curl -fsSL https://ollama.com/install.sh | sh
endif

# pulls any missing model (~2.3 GB); models already here aren't re-checked or updated
models: serve
	$(OLLAMA) list | grep -q llama3.2:3b || $(OLLAMA) pull llama3.2:3b
	$(OLLAMA) list | grep -q nomic-embed-text || $(OLLAMA) pull nomic-embed-text

# starts the Ollama model server if it isn't running (local only, Ollama's default)
serve:
	curl -s localhost:11434 > /dev/null || (nohup $(OLLAMA) serve > /tmp/ollama.log 2>&1 & sleep 3)

# the "it works" check: both models installed, and the model answers
check: serve
	@$(OLLAMA) list | grep -q llama3.2:3b && $(OLLAMA) list | grep -q nomic-embed-text \
	  || { echo "A model is missing: run  make models"; exit 1; }
	@$(OLLAMA) run llama3.2:3b "In one short sentence, say hello to the FDE class." < /dev/null
	@echo "Setup works."
