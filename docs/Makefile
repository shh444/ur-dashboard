PYTHON ?= python

.PHONY: help html clean

help:
	@echo "Targets:"
	@echo "  make html   Build both English and Korean docs into build/html"
	@echo "  make clean  Remove build artifacts"

html:
	$(PYTHON) build_multilang.py

clean:
	rm -rf build
