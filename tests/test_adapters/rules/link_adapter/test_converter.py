"""Tests for the agent skill-link converter.

Тесты конвертера агентских skill-link.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.adapters.rules.link_adapter.converter import (
    LinkConverter,
    SkillLinkConverter,
    SourceLinkConverter,
    ExternalLinkConverter,
)
from ai_skill_manager.entities import LocalSource, Skill, SkillFile, SkillFormat


class TestLinkConverter(unittest.TestCase):
    """Unit tests for LinkConverter and its kind-specific converters."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.converter = LinkConverter()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _make_agent_skill(self, target_dir: Path, name: str, files: dict[str, str] | None = None) -> Skill:
        """Create an Agent-format skill directory under ``target_dir``.

        This mirrors the result of copying a HumanFlat or HumanDir skill into
        the target directory during sync.
        """
        folder = target_dir / name
        folder.mkdir(parents=True, exist_ok=True)
        main = folder / "SKILL.md"
        main.write_text(f"---\nname: {name}\n---\n", encoding="utf-8")
        if files:
            for rel, content in files.items():
                p = folder / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")
        source = LocalSource(scan_path=target_dir)
        return Skill(
            file_path=main,
            folder_path=folder,
            source=source,
            format=SkillFormat.Agent,
            source_path=target_dir,
        )

    def _skill_file(self, skill: Skill, rel_path: str, content: str) -> SkillFile:
        """Write ``content`` into ``skill`` at ``rel_path`` and return a SkillFile."""
        path = skill.folder_path / rel_path
        path.write_text(content, encoding="utf-8")
        return SkillFile(path=path, skill=skill)

    def _first_link(self, skill_file: SkillFile):
        """Return the first parsed link from the skill file."""
        return skill_file.links[0]

    # ------------------------------------------------------------------
    # kind = skill: relative path inside the same skill
    # ------------------------------------------------------------------

    def test_skill_kind_self_link_to_skill_file(self):
        """RU: Ссылка kind=skill на основной файл скилла превращается в ./SKILL.md."""
        target = self.tmpdir / "target"
        skill_a = self._make_agent_skill(target, "skill-a")
        skill_file = self._skill_file(skill_a, "SKILL.md", "[self](./SKILL.md)\n")
        link = self._first_link(skill_file)

        result = self.converter.convert(link, [skill_a])

        self.assertEqual(result, "./SKILL.md")

    def test_skill_kind_internal_link_to_nested_file(self):
        """RU: Ссылка kind=skill на вложенный файл скилла сохраняет относительный путь."""
        target = self.tmpdir / "target"
        skill_a = self._make_agent_skill(target, "skill-a", {"docs/readme.md": "# Doc\n"})
        skill_file = self._skill_file(skill_a, "SKILL.md", "[doc](./docs/readme.md)\n")
        link = self._first_link(skill_file)

        result = self.converter.convert(link, [skill_a])

        self.assertEqual(result, "./docs/readme.md")

    def test_skill_kind_link_with_header(self):
        """RU: Ссылка kind=skill с #header сохраняет заголовок."""
        target = self.tmpdir / "target"
        skill_a = self._make_agent_skill(target, "skill-a")
        skill_file = self._skill_file(skill_a, "SKILL.md", "[self](./SKILL.md#header)\n")
        link = self._first_link(skill_file)

        result = self.converter.convert(link, [skill_a])

        self.assertEqual(result, "./SKILL.md#header")

    # ------------------------------------------------------------------
    # kind = external: keep external URL unchanged
    # ------------------------------------------------------------------

    def test_external_link_unchanged(self):
        """RU: Внешняя ссылка остаётся без изменений."""
        target = self.tmpdir / "target"
        skill_a = self._make_agent_skill(target, "skill-a")
        skill_file = self._skill_file(skill_a, "SKILL.md", "[external](https://example.com)\n")
        link = self._first_link(skill_file)

        result = self.converter.convert(link, [skill_a])

        self.assertEqual(result, "https://example.com")

    def test_external_link_with_header(self):
        """RU: Внешняя ссылка с #fragment сохраняет фрагмент."""
        target = self.tmpdir / "target"
        skill_a = self._make_agent_skill(target, "skill-a")
        skill_file = self._skill_file(skill_a, "SKILL.md", "[external](https://example.com#section)\n")
        link = self._first_link(skill_file)

        result = self.converter.convert(link, [skill_a])

        self.assertEqual(result, "https://example.com#section")

    # ------------------------------------------------------------------
    # kind = source: link to another skill's main file
    # ------------------------------------------------------------------

    def test_source_link_to_other_skill_main_file(self):
        """RU: Ссылка kind=source на основной файл другого скилла -> skill:<name>."""
        target = self.tmpdir / "target"
        skill_a = self._make_agent_skill(target, "skill-a")
        skill_b = self._make_agent_skill(target, "skill-b")
        skill_file = self._skill_file(
            skill_a, "SKILL.md", "[skill-b](../skill-b/SKILL.md)\n"
        )
        link = self._first_link(skill_file)

        result = self.converter.convert(link, [skill_a, skill_b])

        self.assertEqual(result, "skill:skill-b")

    def test_source_link_to_other_skill_main_file_with_header(self):
        """RU: Ссылка kind=source на основной файл другого скилла с #header."""
        target = self.tmpdir / "target"
        skill_a = self._make_agent_skill(target, "skill-a")
        skill_b = self._make_agent_skill(target, "skill-b")
        skill_file = self._skill_file(
            skill_a, "SKILL.md", "[skill-b](../skill-b/SKILL.md#header)\n"
        )
        link = self._first_link(skill_file)

        result = self.converter.convert(link, [skill_a, skill_b])

        self.assertEqual(result, "skill:skill-b#header")

    # ------------------------------------------------------------------
    # kind = source: link to a file nested inside another skill
    # ------------------------------------------------------------------

    def test_source_link_to_nested_file_in_dir_skill(self):
        """RU: Ссылка kind=source на файл внутри директорийного скилла -> skill:name;file:./rel."""
        target = self.tmpdir / "target"
        skill_a = self._make_agent_skill(target, "skill-a")
        skill_b = self._make_agent_skill(
            target, "skill-b", {"docs/extra.md": "# Extra\n"}
        )
        skill_file = self._skill_file(
            skill_a, "SKILL.md", "[extra](../skill-b/docs/extra.md)\n"
        )
        link = self._first_link(skill_file)

        result = self.converter.convert(link, [skill_a, skill_b])

        self.assertEqual(result, "skill:skill-b;file:./docs/extra.md")

    def test_source_link_to_nested_file_in_dir_skill_with_header(self):
        """RU: Ссылка kind=source на файл внутри скилла с #header."""
        target = self.tmpdir / "target"
        skill_a = self._make_agent_skill(target, "skill-a")
        skill_b = self._make_agent_skill(
            target, "skill-b", {"docs/extra.md": "# Extra\n"}
        )
        skill_file = self._skill_file(
            skill_a, "SKILL.md", "[extra](../skill-b/docs/extra.md#header)\n"
        )
        link = self._first_link(skill_file)

        result = self.converter.convert(link, [skill_a, skill_b])

        self.assertEqual(result, "skill:skill-b;file:./docs/extra.md#header")

    # ------------------------------------------------------------------
    # HumanFlat / HumanDir -> Agent conversion cases
    # ------------------------------------------------------------------

    def test_source_link_to_flat_skill_main_file_after_conversion(self):
        """RU: Ссылка на HumanFlat-скилл после копирования в Agent -> skill:name.

        HumanFlat skill: my-skill.skill.md -> Agent: my-skill/SKILL.md.
        Ссылка, разрешённая относительно target_dir, попадает на SKILL.md
        скопированного скилла и должна превратиться в skill:my-skill.
        """
        target = self.tmpdir / "target"
        skill_a = self._make_agent_skill(target, "skill-a")
        # Simulate the Agent-format result of copying a HumanFlat skill.
        skill_b = self._make_agent_skill(target, "my-skill")
        skill_file = self._skill_file(
            skill_a, "SKILL.md", "[flat](../my-skill/SKILL.md)\n"
        )
        link = self._first_link(skill_file)

        result = self.converter.convert(link, [skill_a, skill_b])

        self.assertEqual(result, "skill:my-skill")

    def test_source_link_to_dir_skill_nested_file_after_conversion(self):
        """RU: Ссылка на файл внутри HumanDir-скилла после копирования в Agent.

        HumanDir skill: my-skill.skill/ + my-skill.skill/my-skill.skill.md
        -> Agent: my-skill/ + SKILL.md + docs/extra.md.
        Относительный путь file должен считаться от папки скопированного скилла.
        """
        target = self.tmpdir / "target"
        skill_a = self._make_agent_skill(target, "skill-a")
        # Simulate the Agent-format result of copying a HumanDir skill.
        skill_b = self._make_agent_skill(
            target, "my-skill", {"docs/extra.md": "# Extra\n"}
        )
        skill_file = self._skill_file(
            skill_a, "SKILL.md", "[dir-file](../my-skill/docs/extra.md)\n"
        )
        link = self._first_link(skill_file)

        result = self.converter.convert(link, [skill_a, skill_b])

        self.assertEqual(result, "skill:my-skill;file:./docs/extra.md")

    # ------------------------------------------------------------------
    # Error cases
    # ------------------------------------------------------------------

    def test_source_link_without_matching_skill_raises(self):
        """RU: Ссылка kind=source, не попадающая ни в один скилл, вызывает ValueError."""
        target = self.tmpdir / "target"
        skill_a = self._make_agent_skill(target, "skill-a")
        # A file outside any skill folder.
        orphan = target / "orphan.md"
        orphan.write_text("# Orphan\n", encoding="utf-8")
        skill_file = self._skill_file(
            skill_a, "SKILL.md", "[orphan](../orphan.md)\n"
        )
        link = self._first_link(skill_file)

        with self.assertRaises(ValueError):
            self.converter.convert(link, [skill_a])


class TestSkillLinkConverter(unittest.TestCase):
    """Direct tests for SkillLinkConverter."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.converter = SkillLinkConverter()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_returns_formatted_path(self):
        """RU: SkillLinkConverter возвращает absLink.path.formatted."""
        target = self.tmpdir / "target"
        target.mkdir()
        skill_file_path = target / "SKILL.md"
        skill_file_path.write_text("---\nname: s\n---\n[self](./SKILL.md)\n", encoding="utf-8")
        skill = Skill(
            file_path=skill_file_path,
            folder_path=target,
            source=LocalSource(scan_path=target.parent),
            format=SkillFormat.Agent,
            source_path=target.parent,
        )
        skill_file = SkillFile(path=skill_file_path, skill=skill)
        link = skill_file.links[0]

        result = self.converter.convert(link, [skill])

        self.assertEqual(result, "./SKILL.md")


class TestExternalLinkConverter(unittest.TestCase):
    """Direct tests for ExternalLinkConverter."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.converter = ExternalLinkConverter()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_returns_external_url(self):
        """RU: ExternalLinkConverter возвращает внешний URL."""
        target = self.tmpdir / "target"
        target.mkdir()
        skill_file_path = target / "SKILL.md"
        skill_file_path.write_text(
            "---\nname: s\n---\n[ext](https://example.com)\n", encoding="utf-8"
        )
        skill = Skill(
            file_path=skill_file_path,
            folder_path=target,
            source=LocalSource(scan_path=target.parent),
            format=SkillFormat.Agent,
            source_path=target.parent,
        )
        skill_file = SkillFile(path=skill_file_path, skill=skill)
        link = skill_file.links[0]

        result = self.converter.convert(link, [skill])

        self.assertEqual(result, "https://example.com")


class TestSourceLinkConverter(unittest.TestCase):
    """Direct tests for SourceLinkConverter."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.converter = SourceLinkConverter()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _make_agent_skill(self, target_dir: Path, name: str, files: dict[str, str] | None = None) -> Skill:
        folder = target_dir / name
        folder.mkdir(parents=True, exist_ok=True)
        main = folder / "SKILL.md"
        main.write_text(f"---\nname: {name}\n---\n", encoding="utf-8")
        if files:
            for rel, content in files.items():
                p = folder / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")
        source = LocalSource(scan_path=target_dir)
        return Skill(
            file_path=main,
            folder_path=folder,
            source=source,
            format=SkillFormat.Agent,
            source_path=target_dir,
        )

    def test_main_file_skill_name(self):
        """RU: SourceLinkConverter выдаёт skill:name для основного файла скилла."""
        target = self.tmpdir / "target"
        skill_a = self._make_agent_skill(target, "skill-a")
        skill_b = self._make_agent_skill(target, "skill-b")
        skill_file = SkillFile(path=skill_a.file_path, skill=skill_a)
        skill_a.file_path.write_text(
            "---\nname: skill-a\n---\n[b](../skill-b/SKILL.md)\n", encoding="utf-8"
        )
        link = skill_file.links[0]

        result = self.converter.convert(link, [skill_a, skill_b])

        self.assertEqual(result, "skill:skill-b")


if __name__ == "__main__":
    unittest.main()
