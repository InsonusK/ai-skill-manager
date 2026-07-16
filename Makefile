init:
	bash ./script/init.bash
	bash ./script/pip_install.bash

pip-i:
	bash ./script/pip_install.bash

test:
	.venv/bin/pytest -v

test-codecover:
	.venv/bin/pytest -v --cov=./src --cov-report html

run-check:
	.venv/bin/python -m ai_skill_manager.cli check

run-sync:
	.venv/bin/python -m ai_skill_manager.cli sync

profile-sync:
	cd profiling &&	../.venv/bin/python -m ai_skill_manager.cli --profile sync

profile-check:
	cd profiling &&	../.venv/bin/python -m ai_skill_manager.cli --profile check

profile-view:
	.venv/bin/snakeviz profiling/ai-skill-manager.prof

build:
	python -m build
