"""Tests for SkipFolderExcludeRule default behaviour (examples folder)."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities import LocalSource, Skill, SkillFormat
from ai_skill_manager.models import LinkWithContext
from ai_skill_manager.validators.rules.link.exclude_rule import SkipFolderExcludeRule


class TestExamplesFolderExcludeRule(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.repo_path = self.tmpdir / "repo"
        self.repo_path.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _skill_with_file(self, relative_dir: str, file_name: str = "SKILL.md") -> Skill:
        folder = self.repo_path / relative_dir
        folder.mkdir(parents=True, exist_ok=True)
        file_path = folder / file_name
        file_path.write_text("---\nname: skill\n---\n# Skill\n[file](./file.md)\n")
        return Skill(
            file_path=file_path,
            folder_path=folder,
            source=LocalSource(scan_path=self.repo_path, repo_path=self.repo_path),
            format=SkillFormat.Agent,
            source_path=self.repo_path,
        )

    def _context(self, skill: Skill) -> LinkWithContext:
        skill_file = skill.files[0]
        link = skill_file.links[0]
        return LinkWithContext.build(skill, skill_file, link)

    def test_default_skips_examples_folder(self):
        skill = self._skill_with_file("skill/examples")
        rule = SkipFolderExcludeRule()

        self.assertTrue(rule.should_exclude(self._context(skill), [skill]))

    def test_default_does_not_skip_other_folders(self):
        skill = self._skill_with_file("skill/docs")
        rule = SkipFolderExcludeRule()

        self.assertFalse(rule.should_exclude(self._context(skill), [skill]))

    def test_empty_list_disables_exclusions(self):
        skill = self._skill_with_file("skill/examples")
        rule = SkipFolderExcludeRule(skip_folders=[])

        self.assertFalse(rule.should_exclude(self._context(skill), [skill]))

    def test_custom_folder_overrides_default(self):
        skill = self._skill_with_file("skill/another_folder")
        rule = SkipFolderExcludeRule(skip_folders=["another_folder"])

        self.assertTrue(rule.should_exclude(self._context(skill), [skill]))

    def test_custom_folder_does_not_skip_examples(self):
        skill = self._skill_with_file("skill/examples")
        rule = SkipFolderExcludeRule(skip_folders=["another_folder"])

        self.assertFalse(rule.should_exclude(self._context(skill), [skill]))


if __name__ == "__main__":
    unittest.main()
