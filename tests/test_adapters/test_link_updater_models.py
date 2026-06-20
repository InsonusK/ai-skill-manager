"""Tests for link updater model classes."""

import pytest
from pathlib import Path

from ai_skill_manager.adapters.link_updater.models.file_context import FileContext
from ai_skill_manager.models import LocalSource, Skill, SkillFormat


def _skill(file_path: Path, folder_path: Path | None = None) -> Skill:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if not file_path.exists():
        file_path.write_text("---\nname: test\n---\n")
    if folder_path is None:
        skill_format = SkillFormat.HumanFlat
    elif file_path.name == "SKILL.md":
        skill_format = SkillFormat.Agent
    else:
        skill_format = SkillFormat.HumanDir
    return Skill(
        file_path=file_path,
        folder_path=folder_path,
        format=skill_format,
        source=LocalSource(folder_path if folder_path else file_path.parent),
    )


class TestFileContext:
    def test_stores_path_and_skill(self, tmp_path: Path):
        skill_md = tmp_path / "my.skill.md"
        skill = _skill(skill_md)

        ctx = FileContext(path=skill_md, skill=skill)

        assert ctx.path == skill_md
        assert ctx.skill == skill
        assert ctx.content is None

    def test_stores_content(self, tmp_path: Path):
        skill_md = tmp_path / "my.skill.md"
        skill = _skill(skill_md)

        ctx = FileContext(path=skill_md, skill=skill, content="# Hello")

        assert ctx.content == "# Hello"

    def test_skill_may_be_none(self, tmp_path: Path):
        skill_md = tmp_path / "my.skill.md"

        ctx = FileContext(path=skill_md, skill=None)

        assert ctx.path == skill_md
        assert ctx.skill is None
