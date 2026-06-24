init:
	bash ./script/init.bash
	bash ./script/pip_install.bash

pip-i:
	bash ./script/pip_install.bash

test:
	.venv/bin/pytest -v

test-codecover:
	.venv/bin/pytest -v --cov=./src --cov-report html

run-ai-skill-manager:
	.venv/bin/python -m ai_skill_manager.cli sync

profile-sync:
	.venv/bin/python -m ai_skill_manager.cli --profile sync

profile-discover:
	.venv/bin/python -m ai_skill_manager.cli --profile discover
