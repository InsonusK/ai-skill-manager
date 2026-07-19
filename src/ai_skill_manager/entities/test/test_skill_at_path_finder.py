"""Tests for SkillAtPathFinder."""

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_skill_manager.entities.skill_at_path_finder import SkillAtPathFinder
from ai_skill_manager.entities.skill_kind import SkillKind
from ai_skill_manager.service.skill_discovery.skill.auto import AutoDiscovery
from ai_skill_manager.tools.path_utils import same_path


class TestSkillAtPathFinder(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.finder = SkillAtPathFinder()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_finds_flat_skill_at_its_own_file(self):
        md = self.tmp / "guide.skill.md"
        md.write_text("---\nname: guide\n---\n")

        result = self.finder.find(md, self.tmp)

        self.assertIsNotNone(result)
        self.assertEqual(result.name, "guide")
        self.assertEqual(result.kind, SkillKind.flat)

    def test_finds_dir_skill_at_its_folder(self):
        folder = self.tmp / "web"
        folder.mkdir()
        (folder / "SKILL.md").write_text("---\nname: web\n---\n")

        result = self.finder.find(folder, self.tmp)

        self.assertIsNotNone(result)
        self.assertEqual(result.name, "web")
        self.assertEqual(result.kind, SkillKind.dir)

    def test_finds_dir_skill_at_its_main_file_directly(self):
        folder = self.tmp / "web"
        folder.mkdir()
        main_file = folder / "SKILL.md"
        main_file.write_text("---\nname: web\n---\n")

        result = self.finder.find(main_file, self.tmp)

        self.assertIsNotNone(result)
        self.assertEqual(result.name, "web")
        self.assertEqual(result.kind, SkillKind.dir)

    def test_returns_none_for_a_plain_file(self):
        plain = self.tmp / "notes.md"
        plain.write_text("# notes\n")

        result = self.finder.find(plain, self.tmp)

        self.assertIsNone(result)

    def test_returns_none_for_a_plain_directory(self):
        plain = self.tmp / "assets"
        plain.mkdir()
        (plain / "image.png").write_text("png")

        result = self.finder.find(plain, self.tmp)

        self.assertIsNone(result)

    def test_finds_dir_skill_by_walking_up_from_a_nested_file(self):
        skill_dir = self.tmp / "some_skill_dir.skill"
        skill_dir.mkdir()
        (skill_dir / "some_skill_dir.skill.md").write_text(
            "---\nname: some-skill-dir\n---\n"
        )
        nested = skill_dir / "subfolder1" / "subfolder2"
        nested.mkdir(parents=True)
        target_file = nested / "some_file"
        target_file.write_text("content")

        result = self.finder.find(target_file, self.tmp)

        self.assertIsNotNone(result)
        self.assertEqual(result.name, "some-skill-dir")
        self.assertEqual(result.kind, SkillKind.dir)
        self.assertEqual(result.repo_path, self.tmp.resolve())

    def test_does_not_walk_above_repo_path(self):
        outer_skill_dir = self.tmp / "outer.skill"
        outer_skill_dir.mkdir()
        (outer_skill_dir / "outer.skill.md").write_text("---\nname: outer\n---\n")
        repo_root = outer_skill_dir / "repo"
        nested = repo_root / "subfolder"
        nested.mkdir(parents=True)
        target_file = nested / "some_file"
        target_file.write_text("content")

        result = self.finder.find(target_file, repo_root)

        self.assertIsNone(result)

    def test_returns_none_when_no_skill_up_to_repo_root(self):
        nested = self.tmp / "a" / "b" / "c"
        nested.mkdir(parents=True)
        target_file = nested / "some_file"
        target_file.write_text("content")

        result = self.finder.find(target_file, self.tmp)

        self.assertIsNone(result)

    def test_caches_scan_result_per_directory(self):
        folder = self.tmp / "web"
        folder.mkdir()
        (folder / "SKILL.md").write_text("---\nname: web\n---\n")

        with patch.object(
            AutoDiscovery,
            "skill_rooted_at",
            autospec=True,
            side_effect=AutoDiscovery.skill_rooted_at,
        ) as mocked_check:
            self.finder.find(folder, self.tmp)
            self.finder.find(folder, self.tmp)

        self.assertEqual(mocked_check.call_count, 1)

    def test_finds_dir_skill_for_a_loose_file_directly_inside_it(self):
        skill_dir = self.tmp / "web.skill"
        skill_dir.mkdir()
        (skill_dir / "web.skill.md").write_text("---\nname: web\n---\n")
        loose_file = skill_dir / "notes.md"
        loose_file.write_text("# notes\n")

        result = self.finder.find(loose_file, self.tmp)

        self.assertIsNotNone(result)
        self.assertEqual(result.name, "web")
        self.assertEqual(result.kind, SkillKind.dir)

    def test_finds_dir_skill_when_linked_directly_to_its_own_human_dir_main_file(self):
        # EN: A HumanDir skill's own main file (`{name}.skill/{name}.skill.md`)
        # also matches the flat `*.skill.md` pattern by name alone. A link
        # pointing straight at that file must still resolve to the *same*
        # directory skill (kind=dir, path=the folder) that a full source
        # scan would have discovered - not a second, distinct flat-kind
        # Skill for the same file, which would falsely look like a
        # different skill with a colliding name.
        # RU: Собственный основной файл HumanDir-скилла
        # (`{name}.skill/{name}.skill.md`) тоже совпадает с плоским
        # паттерном `*.skill.md` по одному имени. Ссылка, указывающая прямо
        # на этот файл, должна по-прежнему разрешаться в тот же самый
        # директориальный скилл (kind=dir, path=папка), который был бы
        # обнаружен полным сканированием источника - а не во второй,
        # отдельный плоский Skill для того же файла, который выглядел бы
        # как другой скилл с конфликтующим именем.
        skill_dir = self.tmp / "plateau-create-by-solutions.skill"
        skill_dir.mkdir()
        main_file = skill_dir / "plateau-create-by-solutions.skill.md"
        main_file.write_text("---\nname: plateau-create-by-solutions\n---\n")

        result = self.finder.find(main_file, self.tmp)

        self.assertIsNotNone(result)
        self.assertEqual(result.name, "plateau-create-by-solutions")
        self.assertEqual(result.kind, SkillKind.dir)
        # same_path(), not a raw Path ==: on Windows, os.path.resolve() can
        # normalize to the short 8.3 form (e.g. RUNNER~1) while skill_dir
        # here still uses the long form, and the two must still compare equal.
        # same_path(), а не сравнение Path напрямую: на Windows
        # os.path.resolve() может привести путь к короткой 8.3-форме
        # (например, RUNNER~1), тогда как skill_dir здесь остаётся в
        # длинной форме, и оба варианта должны считаться равными.
        self.assertTrue(same_path(result.path, skill_dir))

    def test_sibling_subtree_with_a_skill_does_not_affect_resolution(self):
        folder1 = self.tmp / "folder1"
        (folder1 / "folder1-1").mkdir(parents=True)
        target_file = folder1 / "folder1-1" / "target_file"
        target_file.write_text("content")
        sibling = folder1 / "folder1-2"
        sibling.mkdir()
        (sibling / "some_skill.skill.md").write_text("---\nname: some-skill\n---\n")

        result = self.finder.find(target_file, self.tmp)

        self.assertIsNone(result)

    def test_raises_when_the_owning_skill_has_a_nested_skill(self):
        skill_dir = self.tmp / "some_root.skill"
        skill_dir.mkdir()
        (skill_dir / "some_root.skill.md").write_text("---\nname: some-root\n---\n")
        target_file = skill_dir / "folder1" / "folder1-1" / "target_file"
        target_file.parent.mkdir(parents=True)
        target_file.write_text("content")
        nested_skill_dir = skill_dir / "folder1" / "folder1-2"
        nested_skill_dir.mkdir()
        (nested_skill_dir / "some_skill.skill.md").write_text(
            "---\nname: some-skill\n---\n"
        )

        with self.assertRaises(ValueError):
            self.finder.find(target_file, self.tmp)


if __name__ == "__main__":
    unittest.main()
