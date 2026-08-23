.PHONY: venv test lint format clean help build publish smoke-test

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
RUFF := $(VENV)/bin/ruff
ANSIBLE_LINT := $(VENV)/bin/ansible-lint

# Namespace and name for Ansible collection
NAMESPACE := hellqvio86
COLLECTION_NAME := unifi
VERSION ?= $(shell grep '^version:' galaxy.yml | awk '{print $$2}')
GALAXY_API_KEY ?=

export ANSIBLE_HOME ?= $(CURDIR)/.ansible
export ANSIBLE_LOCAL_TEMP ?= $(CURDIR)/.ansible/tmp
export ANSIBLE_REMOTE_TMP ?= $(CURDIR)/.ansible/tmp
export ANSIBLE_COLLECTIONS_PATH ?= $(CURDIR)/.ansible/collections:$(CURDIR)

help:
	@echo "Available targets:"
	@echo "  venv        Create virtual environment and install dependencies"
	@echo "  test        Run unit tests"
	@echo "  lint        Run ruff and ansible-lint"
	@echo "  format      Run ruff format"
	@echo "  clean       Remove virtual environment and cache files"
	@echo "  build       Build the Ansible collection tarball"
	@echo "  smoke-test  Build and test installation into clean location"
	@echo "  publish     Publish the collection to Ansible Galaxy"

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

lint: venv setup-structure
	$(RUFF) check .
	ANSIBLE_HOME=.ansible ANSIBLE_LOCAL_TEMP=.ansible/tmp $(ANSIBLE_LINT) .

format: venv
	$(RUFF) format .

clean:
	rm -rf $(VENV)
	rm -rf ansible_collections
	rm -rf .ruff_cache
	rm -rf .pytest_cache
	rm -rf releases
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -f $(NAMESPACE)-$(COLLECTION_NAME)-*.tar.gz

build: venv
	@mkdir -p releases
	$(VENV)/bin/ansible-galaxy collection build --force --output-path releases/

smoke-test: build
	@echo "Testing collection installation from build artifact..."
	$(VENV)/bin/ansible-galaxy collection install releases/$(NAMESPACE)-$(COLLECTION_NAME)-$(VERSION).tar.gz --force

publish: build
	@if [ -z "$(GALAXY_API_KEY)" ] && [ -z "$$ANSIBLE_GALAXY_API_KEY" ]; then \
		echo "Error: GALAXY_API_KEY environment variable is not set."; \
		echo "Usage: make publish GALAXY_API_KEY=your_api_key [VERSION=0.0.3]"; \
		exit 1; \
	fi
	ANSIBLE_GALAXY_API_KEY=$${ANSIBLE_GALAXY_API_KEY:-$(GALAXY_API_KEY)} $(VENV)/bin/ansible-galaxy collection publish releases/$(NAMESPACE)-$(COLLECTION_NAME)-$(VERSION).tar.gz
