ifdef VIRTUAL_ENV
PYTHON := python
PIP := pip
else
PYTHON := .venv/bin/python
PIP := .venv/bin/pip
endif

WITH_CODE_COVERAGE ?= false
ONLY_DELTA ?= false
DELTA_BASE ?=

.PHONY: init pip-i install test test-codecover cucumber-test mutation-test result-page clean run-check run-sync profile-sync profile-check profile-view build

init:
	bash ./script/init.bash
	bash ./script/pip_install.bash

pip-i:
	bash ./script/pip_install.bash

install:
	$(PIP) install -e ".[dev]"

test:
	$(PYTHON) -m pytest -v

test-codecover:
	$(PYTHON) -m pytest -v --cov=./src --cov-report html

cucumber-test: install
	WITH_CODE_COVERAGE=$(WITH_CODE_COVERAGE) PYTHON=$(PYTHON) scripts/cucumber-test.sh

mutation-test: install
	ONLY_DELTA=$(ONLY_DELTA) DELTA_BASE=$(DELTA_BASE) PYTHON=$(PYTHON) scripts/mutation-test.sh

result-page:
	scripts/result-page.sh

run-check:
	$(PYTHON) -m ai_skill_manager.cli check

run-sync:
	$(PYTHON) -m ai_skill_manager.cli sync

profile-sync:
	cd ./profiling && rm -rf ./tmp && rm -rf ./ai-skill-manager.prof && \
	$(PYTHON) -m ai_skill_manager.cli --profile --profile-output ai-skill-manager.prof sync

profile-check:
	cd ./profiling && rm -rf ./tmp && rm -rf ./ai-skill-manager.prof && \
	$(PYTHON) -m ai_skill_manager.cli --profile --profile-output ai-skill-manager.prof check

profile-view:
	$(PYTHON) -m snakeviz profiling/ai-skill-manager.prof

build:
	$(PYTHON) -m build

clean:
	rm -rf tmp/result tmp/report public .coverage .mutmut-cache mutants
