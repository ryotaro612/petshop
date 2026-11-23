# petshop: set up the repo so ComfyUI can be started with comfy-cli.
# Requires git, uv and Python 3.14 (see comfyui/.python-version). Run from the repo root.

.DEFAULT_GOAL := help

# Keep uv's package cache in the repo, and use the installed Python instead of downloading one.
export UV_CACHE_DIR := $(CURDIR)/.cache/uv
export UV_PYTHON_PREFERENCE := only-system
unexport VIRTUAL_ENV

# Dependencies come from comfyui/uv.lock, so comfy-cli only fetches ComfyUI itself.
# VIRTUAL_ENV makes comfy-cli run ComfyUI with comfyui/.venv instead of creating its own venv.
COMFY := VIRTUAL_ENV=$(CURDIR)/comfyui/.venv comfyui/.venv/bin/comfy-cli --skip-prompt --workspace $(CURDIR)/comfyui/ComfyUI

##@ Setup

setup: comfyui/.venv scripts/.venv comfyui/ComfyUI ## install the dependencies and ComfyUI

comfyui/.venv scripts/.venv: %/.venv: %/uv.lock
	uv sync --project $* --locked
	touch $@

# Order-only: recreating the venv must not re-install ComfyUI.
comfyui/ComfyUI: | comfyui/.venv
	$(COMFY) install --m-series --skip-requirement --skip-torch-or-directml --skip-manager

##@ Run

# comfyui/ComfyUI holds only ComfyUI's code. Settings (user/), models, custom nodes,
# inputs and outputs live in comfyui/ itself, so `make clean` keeps them.
# ComfyUI fails to start if custom_nodes/ is missing from the base directory.
launch: comfyui/.venv comfyui/ComfyUI ## start ComfyUI with comfy-cli, keeping settings and data in comfyui/
	mkdir -p comfyui/custom_nodes
	$(COMFY) launch -- --base-directory $(CURDIR)/comfyui

##@ Clean

clean: ## remove everything that can be downloaded again (keeps comfyui/user, input and output)
	rm -rf comfyui/.venv 

.PHONY: setup launch clean

##@ Help
.PHONY: help
help: ## Display this help.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
