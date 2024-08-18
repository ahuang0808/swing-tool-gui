POETRY_RUN := poetry run
VERSION := $(shell poetry version -s)
export PYTHONPATH := $(shell pwd)

.DEFAULT_GOAL := help

help:  ## print this help
	@# https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
	@grep -E '^[a-zA-Z_/-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
	@echo ""
.PHONY: help

run:    ## Run the app

	$(POETRY_RUN) python swing_tool_gui/app.py
.PHONY: format

lint:    ## Check lint
	$(POETRY_RUN) ruff check
.PHONY: lint

format:    ## Fix lint
	$(POETRY_RUN) ruff format
.PHONY: format

build:    ## Build the app
	$(POETRY_RUN) pyinstaller --name swing_tool_gui --windowed swing_tool_gui/app.py --noconfirm --strip --clean --collect-all=swing_tool
.PHONY: build

release:    ## Create new tag
	git tag v${VERSION}
	git push origin v${VERSION}
.PHONY: release
