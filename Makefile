ifdef VIRTUAL_ENV
PYTHON := python
PYTEST := pytest
SNAKEVIZ := snakeviz
else
PYTHON := .venv/bin/python
PYTEST := .venv/bin/pytest
SNAKEVIZ := .venv/bin/snakeviz
endif

init:
	bash ./script/init.bash
	bash ./script/pip_install.bash

pip-i:
	bash ./script/pip_install.bash

test:
	$(PYTEST) -v

test-codecover:
	$(PYTEST) -v --cov=./src --cov-report html

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
	$(SNAKEVIZ) profiling/ai-skill-manager.prof

build:
	$(PYTHON) -m build
