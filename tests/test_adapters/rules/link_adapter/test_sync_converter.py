"""Integration tests for link conversion using real source/target fixtures.

Интеграционные тесты конвертации ссылок на реальных фикстурах source/target.

Fixtures are grouped by raw path kind:

- ``mocks/relative/`` — links written as ``./path`` or ``../path``
- ``mocks/repo_absolute/`` — links written as ``repo/path`` (relative to the repository root)
- ``mocks/os_absolute/`` — links written as ``/absolute/path``

Each fixture directory contains:
- ``source/`` — a sample source tree passed to ``run_sync``
- ``target/`` — the expected ``.agents/skills`` tree after synchronization
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities import LocalSource
from ai_skill_manager.services.sync import run_sync


MOCKS_DIR = Path(__file__).parent / "mocks"


class _SyncFixtureHelper(unittest.TestCase):
    """Shared helpers for running sync on a fixture and comparing results."""

    path_type: str = ""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _run_sync_case(self, case_name: str):
        """Run sync for ``case_name`` and return the produced target dir."""
        case_dir = MOCKS_DIR / self.path_type / case_name
        source_dir = case_dir / "source"
        target_dir = self.tmpdir / "target"

        result = run_sync([LocalSource(scan_path=source_dir)], target_dir)
        self.assertEqual(result["skills_count"], 2)
        return target_dir

    def _assert_skill_md_equal(self, actual_dir: Path, expected_dir: Path, skill_name: str):
        """Compare the SKILL.md content of ``skill_name`` in actual and expected trees."""
        actual = (actual_dir / skill_name / "SKILL.md").read_text(encoding="utf-8")
        expected = (expected_dir / skill_name / "SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(actual, expected)


class TestRelative(_SyncFixtureHelper):
    """Tests for relative links (``./path`` and ``../path``)."""

    path_type = "relative"

    def test_cross_skill_source_to_target(self):
        """RU: Относительная ссылка на другой скилл корректно маппится.

        Исходный путь: ``../skill-b/skill-b.skill.md``
        После синхронизации: ``skill:skill-b``
        """
        target_dir = self._run_sync_case("cross_skill_source_to_target")
        expected_dir = MOCKS_DIR / self.path_type / "cross_skill_source_to_target" / "target"

        self._assert_skill_md_equal(target_dir, expected_dir, "skill-a")
        self._assert_skill_md_equal(target_dir, expected_dir, "skill-b")

    def test_source_link_to_nested_file(self):
        """RU: Относительная ссылка на вложенный файл другого скилла.

        Исходный путь: ``../skill-b.skill/docs/extra.md``
        После синхронизации: ``skill:skill-b;file:./docs/extra.md``
        """
        target_dir = self._run_sync_case("source_link_to_nested_file")
        expected_dir = MOCKS_DIR / self.path_type / "source_link_to_nested_file" / "target"

        self._assert_skill_md_equal(target_dir, expected_dir, "skill-a")
        self._assert_skill_md_equal(target_dir, expected_dir, "skill-b")
        self.assertEqual(
            (target_dir / "skill-b" / "docs" / "extra.md").read_text(encoding="utf-8"),
            (expected_dir / "skill-b" / "docs" / "extra.md").read_text(encoding="utf-8"),
        )

    def test_human_flat_to_agent(self):
        """RU: Относительная ссылка на HumanFlat-скилл после копирования.

        Исходный путь: ``../skill-b.skill.md``
        После синхронизации: ``skill:skill-b``
        """
        target_dir = self._run_sync_case("human_flat_to_agent")
        expected_dir = MOCKS_DIR / self.path_type / "human_flat_to_agent" / "target"

        self._assert_skill_md_equal(target_dir, expected_dir, "skill-a")
        self._assert_skill_md_equal(target_dir, expected_dir, "skill-b")

    def test_human_dir_to_agent(self):
        """RU: Относительная ссылка на HumanDir-скилл после копирования.

        Исходный путь: ``../skill-b.skill/skill-b.skill.md``
        После синхронизации: ``skill:skill-b``
        """
        target_dir = self._run_sync_case("human_dir_to_agent")
        expected_dir = MOCKS_DIR / self.path_type / "human_dir_to_agent" / "target"

        self._assert_skill_md_equal(target_dir, expected_dir, "skill-a")
        self._assert_skill_md_equal(target_dir, expected_dir, "skill-b")


class TestRepoAbsolute(_SyncFixtureHelper):
    """Tests for repo-absolute links (paths relative to the repository root)."""

    path_type = "repo_absolute"

    def test_repo_absolute_to_skill_folder(self):
        """RU: repo-absolute ссылка на папку HumanDir-скилла без .md.

        Исходный путь: ``skills/category/module-api-csproj.skill``
        После синхронизации: ``skill:module-api-csproj``
        """
        target_dir = self._run_sync_case("repo_absolute_to_skill_folder")
        expected_dir = MOCKS_DIR / self.path_type / "repo_absolute_to_skill_folder" / "target"

        self._assert_skill_md_equal(target_dir, expected_dir, "other-skill")
        self._assert_skill_md_equal(target_dir, expected_dir, "module-api-csproj")

    def test_curly_braces_skill_folder(self):
        """RU: repo-absolute ссылка на папку скилла с фигурными скобками.

        Исходный путь:
        ``skills/dotnet/architecture/plateau/default/{Module}.Api/module-api-csproj.skill``
        После синхронизации: ``skill:module-api-csproj``
        """
        target_dir = self._run_sync_case("curly_braces_skill_folder")
        expected_dir = MOCKS_DIR / self.path_type / "curly_braces_skill_folder" / "target"

        self._assert_skill_md_equal(target_dir, expected_dir, "other-skill")
        self._assert_skill_md_equal(target_dir, expected_dir, "module-api-csproj")

    def test_source_link_to_deep_nested_file(self):
        """RU: repo-absolute ссылка на вложенный файл HumanDir-скилла.

        Исходный путь:
        ``skills/category/solution-structure-solution/Implementation/Repository.create.md``
        После синхронизации:
        ``skill:solution-structure-solution;file:./Implementation/Repository.create.md``
        """
        target_dir = self._run_sync_case("source_link_to_deep_nested_file")
        expected_dir = MOCKS_DIR / self.path_type / "source_link_to_deep_nested_file" / "target"

        self._assert_skill_md_equal(target_dir, expected_dir, "other-skill")
        self._assert_skill_md_equal(target_dir, expected_dir, "solution-structure-solution")
        self.assertEqual(
            (target_dir / "solution-structure-solution" / "Implementation" / "Repository.create.md").read_text(encoding="utf-8"),
            (expected_dir / "solution-structure-solution" / "Implementation" / "Repository.create.md").read_text(encoding="utf-8"),
        )

    def test_deep_nested_source_to_target(self):
        """RU: Глубоко вложенный repo-absolute путь корректно маппится.

        Исходный путь:
        ``skills/dotnet/architecture/solutions/🧩validated/entity-concurrency-change-solution.skill/entity-concurrency-change-solution.skill.md``
        После синхронизации: ``skill:entity-concurrency-change-solution``
        """
        target_dir = self._run_sync_case("deep_nested_source_to_target")
        expected_dir = MOCKS_DIR / self.path_type / "deep_nested_source_to_target" / "target"

        self._assert_skill_md_equal(target_dir, expected_dir, "other-skill")
        self._assert_skill_md_equal(
            target_dir, expected_dir, "entity-concurrency-change-solution"
        )


class TestOsAbsolute(_SyncFixtureHelper):
    """Tests for OS-absolute links (paths starting with ``/``)."""

    path_type = "os_absolute"

    def test_os_absolute_outside_repo_copies_to_files(self):
        """RU: OS-absolute ссылка на файл вне репозитория копируется в files/.

        Исходный путь: ``/tmp/.../external.md``
        После синхронизации: ``./files/external.md`` и файл в ``files/``.
        """
        case_dir = MOCKS_DIR / self.path_type / "os_absolute"
        source_dir = self.tmpdir / "source"
        shutil.copytree(case_dir / "source", source_dir)
        target_dir = self.tmpdir / "target"

        external_file = self.tmpdir / "external.md"
        external_file.write_text("# External\n", encoding="utf-8")

        skill_a_md = source_dir / "skills" / "category" / "skill-a.skill" / "skill-a.skill.md"
        skill_a_md.write_text(
            f"---\nname: skill-a\n---\n# Skill A\n[link]({external_file.as_posix()})\n",
            encoding="utf-8",
        )

        result = run_sync([LocalSource(scan_path=source_dir)], target_dir)
        self.assertEqual(result["skills_count"], 2)

        actual = (target_dir / "skill-a" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(f"[link](./files/external.md)", actual)
        self.assertTrue((target_dir / "skill-a" / "files" / "external.md").exists())
        self.assertEqual(
            (target_dir / "skill-a" / "files" / "external.md").read_text(encoding="utf-8"),
            "# External\n",
        )


if __name__ == "__main__":
    unittest.main()
