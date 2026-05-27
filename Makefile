init:
	bash ./script/bash

test:
	.venv/bin/pytest -v

test-codecover:
	.venv/bin/pytest -v --cov=./src --cov-report html

run-ai-skills:
	.venv/bin/python -m ai_skills_manager.cli sync
