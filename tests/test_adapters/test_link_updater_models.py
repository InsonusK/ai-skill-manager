"""Tests for link updater model classes."""

import pytest
from pathlib import Path

from ai_skill_manager.adapters.link_updater.models.FileContext import FileContext
from ai_skill_manager.models import LocalSource, Skill


def _skill(file_path: Path, folder_path: Path | None = None) -> Skill:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if not file_path.exists():
        file_path.write_text("---\nname: test\n---\n")
    return Skill(
        file_path=file_path,
        folder_path=folder_path,
        source=LocalSource(folder_path if folder_path else file_path.parent),
    )


class TestFileContext:
    def test_flat_skill_with_matching_path(self, tmp_path: Path):
        skill_md = tmp_path / "my.skill.md"
        skill = _skill(skill_md)

        ctx = FileContext(path=skill_md, skill=skill)

        assert ctx.path == skill_md
        assert ctx.skill == skill

    def test_flat_skill_with_mismatching_path_raises(self, tmp_path: Path):
        skill_md = tmp_path / "my.skill.md"
        other_file = tmp_path / "other.md"
        skill = _skill(skill_md)

        with pytest.raises(ValueError, match="Flat skill path must equal"):
            FileContext(path=other_file, skill=skill)

    def test_directory_skill_with_sub_path(self, tmp_path: Path):
        skill_dir = tmp_path / "my_skill"
        skill_dir.mkdir()
        skill_md = skill_dir / "SKILL.md"
        sub_file = skill_dir / "docs" / "page.md"
        sub_file.parent.mkdir(parents=True, exist_ok=True)
        sub_file.write_text("# page")
        skill = _skill(skill_md, folder_path=skill_dir)

        ctx = FileContext(path=sub_file, skill=skill)

        assert ctx.path == sub_file

    def test_directory_skill_with_path_outside_folder_raises(self, tmp_path: Path):
        skill_dir = tmp_path / "my_skill"
        skill_dir.mkdir()
        skill_md = skill_dir / "SKILL.md"
        outside_file = tmp_path / "outside.md"
        outside_file.write_text("# outside")
        skill = _skill(skill_md, folder_path=skill_dir)

        with pytest.raises(ValueError, match="Path must be inside skill folder"):
            FileContext(path=outside_file, skill=skill)
