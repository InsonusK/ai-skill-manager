"""Tests for LinkValidationRule."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities import LocalSource, Skill, SkillFormat
from ai_skill_manager.validators.rules.link_validation_rule import LinkValidationRule


MOCK_DIR = Path(__file__).parent.parent / "mock" / "test_link_validation_rule"


class TestLinkValidationRule(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _copy_mock(self, name: str) -> Path:
        src = MOCK_DIR / name
        dst = self.tmpdir / name
        shutil.copytree(src, dst)
        return dst

    def _skill(self, file_path: Path, folder_path: Path | None = None) -> Skill:
        repo_path = file_path.parent.parent if folder_path else file_path.parent
        return Skill(
            file_path=file_path,
            folder_path=folder_path,
            source=LocalSource(scan_path=file_path.parent, repo_path=repo_path),
            format=SkillFormat.Agent if folder_path else SkillFormat.HumanFlat,
            source_path=file_path.parent,
        )

    def _dir_skill(self, root: Path, name: str) -> Skill:
        skill_dir = root / name
        return self._skill(skill_dir / "SKILL.md", skill_dir)

    def test_internal_link_is_valid(self):
        root = self._copy_mock("internal_link")
        skill = self._dir_skill(root, "skill")

        rule = LinkValidationRule()
        result = rule.validate([skill])

        self.assertEqual(result, {})

    def test_cross_skill_link_is_valid(self):
        root = self._copy_mock("cross_skill")
        a = self._dir_skill(root, "skill-a")
        b = self._dir_skill(root, "skill-b")

        rule = LinkValidationRule()
        result = rule.validate([a, b])

        self.assertEqual(result, {})

    def test_cross_skill_non_md_file_link_is_valid(self):
        # EN: A link to a non-markdown file inside another included skill must
        # be valid, because such files are copied together with the skill.
        # RU: Ссылка на не-markdown файл внутри другого включённого скилла
        # должна считаться корректной, так как такие файлы копируются вместе со
        # скиллом.
        root = self._copy_mock("cross_skill_non_md")
        a = self._dir_skill(root, "skill-a")
        b = self._dir_skill(root, "skill-b")

        rule = LinkValidationRule()
        result = rule.validate([a, b])

        self.assertEqual(result, {})

    def test_external_url_is_valid(self):
        root = self._copy_mock("external_url")
        skill = self._dir_skill(root, "skill")

        rule = LinkValidationRule()
        result = rule.validate([skill])

        self.assertEqual(result, {})

    def test_link_outside_skill_set_is_invalid(self):
        root = self._copy_mock("outside_skill")
        skill = self._dir_skill(root, "skill")

        rule = LinkValidationRule()
        result = rule.validate([skill])

        self.assertIn(skill, result)
        self.assertTrue(result[skill].has_errors)

    def test_missing_file_is_invalid(self):
        # EN: A link to a file that does not exist must produce a validation error.
        # RU: Ссылка на несуществующий файл должна давать ошибку валидации.
        root = self._copy_mock("internal_link")
        skill_dir = root / "skill"
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            "---\nname: skill\n---\n# Skill\n[missing](./missing.md)\n"
        )
        skill = self._dir_skill(root, "skill")

        rule = LinkValidationRule()
        result = rule.validate([skill])

        self.assertIn(skill, result)
        self.assertTrue(result[skill].has_errors)

    def test_source_file_outside_skill_is_valid(self):
        # EN: A link to an existing file outside any skill is valid even though
        # the file is not part of a skill directory.
        # RU: Ссылка на существующий файл вне любого скилла валидна, даже
        # если файл не входит в директорию скилла.
        root = self._copy_mock("outside_skill")
        (root / "orphan.md").write_text("# Orphan\n")
        skill_dir = root / "skill"
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            "---\nname: skill\n---\n# Skill\n[orphan](../orphan.md)\n"
        )
        skill = self._dir_skill(root, "skill")

        rule = LinkValidationRule()
        result = rule.validate([skill])

        self.assertEqual(result, {})

    def test_os_file_is_valid(self):
        # EN: A link to an existing OS-absolute file outside the repository is
        # valid.
        # RU: Ссылка на существующий OS-абсолютный файл вне репозитория валидна.
        root = self._copy_mock("internal_link")
        external = self.tmpdir / "external.md"
        external.write_text("# External\n")
        skill_dir = root / "skill"
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            f"---\nname: skill\n---\n# Skill\n[external]({external.as_posix()})\n"
        )
        skill = self._dir_skill(root, "skill")

        rule = LinkValidationRule()
        result = rule.validate([skill])

        self.assertEqual(result, {})

    def test_wiki_link_to_other_skill_is_valid(self):
        root = self._copy_mock("wiki_link")
        a = self._dir_skill(root, "skill-a")
        b = self._dir_skill(root, "skill-b")

        rule = LinkValidationRule()
        result = rule.validate([a, b])

        self.assertEqual(result, {})

    def test_fragment_only_wiki_link_is_valid(self):
        # EN: A wiki link that contains only a fragment (e.g. [[#Header]]) must
        # be treated as a link to the current skill file and therefore be valid.
        # RU: Wiki-ссылка, содержащая только фрагмент (например, [[#Заголовок]]),
        # должна считаться ссылкой на текущий файл скилла и быть корректной.
        root = self._copy_mock("fragment_only_link")
        skill = self._dir_skill(root, "skill")

        rule = LinkValidationRule()
        result = rule.validate([skill])

        self.assertEqual(result, {})

    def test_windows_separator_internal_link_is_valid(self):
        # EN: A link written with Windows backslashes to a file inside the same
        # skill must be valid, just like a POSIX-style link.
        # RU: Ссылка с обратными слешами Windows на файл внутри того же скилла
        # должна считаться корректной, как и POSIX-ссылка.
        root = self._copy_mock("internal_link")
        skill_dir = root / "skill"
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            "---\nname: skill\n---\n# Skill\n[template](.\\template.md)\n"
        )
        skill = self._dir_skill(root, "skill")

        rule = LinkValidationRule()
        result = rule.validate([skill])

        self.assertEqual(result, {})

    def test_windows_separator_cross_skill_link_is_valid(self):
        # EN: A link written with Windows backslashes to a file inside another
        # skill in the sync set must be valid.
        # RU: Ссылка с обратными слешами Windows на файл внутри другого скилла,
        # входящего в копирование, должна считаться корректной.
        root = self._copy_mock("cross_skill_non_md")
        a = self._dir_skill(root, "skill-a")
        b = self._dir_skill(root, "skill-b")
        skill_file = a.folder_path / "SKILL.md"
        skill_file.write_text(
            "---\nname: skill-a\n---\n# A\n[impl](.\\..\\skill-b\\Implementation\\App.Host.csproj.extend.md)\n"
        )

        rule = LinkValidationRule()
        result = rule.validate([a, b])

        self.assertEqual(result, {})

    def test_link_in_plain_text_is_validated(self):
        # EN: A link in regular markdown text must be validated.
        # RU: Ссылка в обычном markdown-тексте должна проверяться.
        root = self._copy_mock("internal_link")
        skill_dir = root / "skill"
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            "---\nname: skill\n---\n# Skill\n[missing](./missing.md)\n"
        )
        skill = self._dir_skill(root, "skill")

        rule = LinkValidationRule()
        result = rule.validate([skill])

        self.assertIn(skill, result)
        self.assertTrue(result[skill].has_errors)

    def test_link_in_inline_code_is_skipped(self):
        # EN: A link wrapped in single backticks must not be validated.
        # RU: Ссылка внутри одиночных обратных кавычек не должна проверяться.
        root = self._copy_mock("internal_link")
        skill_dir = root / "skill"
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            "---\nname: skill\n---\n# Skill\n`[missing](./missing.md)`\n"
        )
        skill = self._dir_skill(root, "skill")

        rule = LinkValidationRule()
        result = rule.validate([skill])

        self.assertEqual(result, {})

    def test_link_in_plain_fenced_block_is_validated(self):
        # EN: A link inside a plain fenced code block (no language label) must
        # still be validated.
        # RU: Ссылка внутри обычного fenced code block (без метки языка) должна
        # всё ещё проверяться.
        root = self._copy_mock("internal_link")
        skill_dir = root / "skill"
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            "---\nname: skill\n---\n# Skill\n```\n[missing](./missing.md)\n```\n"
        )
        skill = self._dir_skill(root, "skill")

        rule = LinkValidationRule()
        result = rule.validate([skill])

        self.assertIn(skill, result)
        self.assertTrue(result[skill].has_errors)

    def test_link_in_example_fenced_block_is_skipped(self):
        # EN: A link inside an ```example block must not be validated because
        # such blocks are masked during link discovery.
        # RU: Ссылка внутри блока ```example не должна проверяться, так как
        # такие блоки маскируются при поиске ссылок.
        root = self._copy_mock("internal_link")
        skill_dir = root / "skill"
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            "---\nname: skill\n---\n# Skill\n```example\n[missing](./missing.md)\n```\n"
        )
        skill = self._dir_skill(root, "skill")

        rule = LinkValidationRule()
        result = rule.validate([skill])

        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
