# petshop: set up the local toolchain from a fresh clone.
# Requires git, uv and Python 3.14 (see comfyui/.python-version). Run from the repo root.

.DEFAULT_GOAL := help

# Keep uv's package cache in the repo, and use the installed Python instead of downloading one.
export UV_CACHE_DIR := $(CURDIR)/.cache/uv
export UV_PYTHON_PREFERENCE := only-system
unexport VIRTUAL_ENV

COMFYUI_REPO := https://github.com/comfyanonymous/ComfyUI.git
# Must match the dependencies locked in comfyui/uv.lock.
COMFYUI_REF := 4c2b826d74a1827f5cc4a706608fc4653ed12972

PORT ?= 8188
COMFY_ARGS ?=

##@ Setup

setup: comfyui deps workflows ## set up everything from a fresh clone

comfyui: ## clone ComfyUI at COMFYUI_REF
	test -d comfyui/ComfyUI || git clone -q --filter=blob:none $(COMFYUI_REPO) comfyui/ComfyUI
	git -C comfyui/ComfyUI checkout -q $(COMFYUI_REF)

deps: ## install the Python dependencies of comfyui/ and scripts/
	uv sync --project comfyui --locked
	uv sync --project scripts --locked

workflows: ## save ComfyUI workflows to the tracked comfyui/workflows/
	mkdir -p comfyui/ComfyUI/user/default
	rmdir comfyui/ComfyUI/user/default/workflows 2>/dev/null || true
	ln -sfn ../../../workflows comfyui/ComfyUI/user/default/workflows

##@ Run

run: ## PORT=<port> COMFY_ARGS=<flags> start ComfyUI on localhost (e.g. COMFY_ARGS=--cpu)
	cd comfyui/ComfyUI && ../.venv/bin/python main.py --listen 127.0.0.1 --port $(PORT) $(COMFY_ARGS)

stop: ## PORT=<port> stop the ComfyUI listening on PORT
	lsof -ti tcp:$(PORT) -sTCP:LISTEN | xargs kill

##@ Clean

clean: ## remove the virtualenvs
	rm -rf comfyui/.venv scripts/.venv

distclean: clean ## also remove the ComfyUI clone and .cache/
	rm -rf comfyui/ComfyUI .cache

.PHONY: setup comfyui deps workflows run stop clean distclean

##@ Help
.PHONY: help
help: ## Display this help.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
