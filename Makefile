.PHONY: venv test lint format clean help

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
RUFF := $(VENV)/bin/ruff
ANSIBLE_LINT := $(VENV)/bin/ansible-lint

# Namespace and name for Ansible collection
NAMESPACE := hellqvio86
COLLECTION_NAME := unifi

help:
	@echo "Available targets:"
	@echo "  venv       Create virtual environment and install dependencies"
	@echo "  test       Run unit tests"
	@echo "  lint       Run ruff and ansible-lint"
	@echo "  format     Run ruff format"
	@echo "  clean      Remove virtual environment and cache files"

$(VENV):
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install ruff ansible-lint pytest pytest-mock pyjwt paramiko ansible-core
	if [ -f requirements.txt ]; then $(PIP) install -r requirements.txt; fi
	if [ -f tests/requirements.txt ]; then $(PIP) install -r tests/requirements.txt; fi

venv: $(VENV)

setup-structure:
	@mkdir -p ansible_collections/$(NAMESPACE)
	@if [ ! -L ansible_collections/$(NAMESPACE)/$(COLLECTION_NAME) ]; then \
		ln -s ../.. ansible_collections/$(NAMESPACE)/$(COLLECTION_NAME); \
	fi

test: venv setup-structure
	PYTHONPATH=. $(PYTEST) tests/unit

lint: venv
	$(RUFF) check .
	$(ANSIBLE_LINT) .

format: venv
	$(RUFF) format .

clean:
	rm -rf $(VENV)
	rm -rf ansible_collections
	rm -rf .ruff_cache
	rm -rf .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
