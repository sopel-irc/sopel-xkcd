.PHONY: build

build:
	rm -rf build/ dist/
	python -m build --sdist --wheel --outdir dist/ .

dev:
	pip install -e .
