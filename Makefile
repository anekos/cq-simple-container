.PHONY: interactive
interactive:
	uv run simple-container -- interactive

.PHONY: build
build:
	axe src/**/*.py -- uv run simple-container -- build

.PHONY: watch
watch:
	axe src/**/*.py -- uv run simple-container -- build --show

.PHONY: setup
setup:
	uv sync
	uv run pre-commit install
