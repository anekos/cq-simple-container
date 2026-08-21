.PHONY: watch
watch:
	axe src/**/*.py -- uv run simple-container -- build --show

.PHONY: build
build:
	axe src/**/*.py -- uv run simple-container -- build
