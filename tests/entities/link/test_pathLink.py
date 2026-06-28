"""Tests for PathLink resolution.

Тесты разрешения путей в PathLink.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.discovery.link.builder.markdown import MarkdownLinkBuilder
from ai_skill_manager.discovery.link.builder.wikilink import WikilinkBuilder
from ai_skill_manager.entities import LocalSource, Skill, SkillFormat
from ai_skill_manager.entities.path_kind import PathKind
from ai_skill_manager.entities.link import PathLink
from ai_skill_manager.entities.link.link_kind import LinkKind
from ai_skill_manager.entities.skill_file import SkillFile


MOCKS_DIR = Path(__file__).parent / "mocks"


class TestPathLink(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.workdir = self.tmpdir / "mocks"
        shutil.copytree(MOCKS_DIR, self.workdir)

        self.flat_dir = self.workdir / "flat"
        self.dir_dir = self.workdir / "dir"
        self.repo_root = self.workdir

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _skill(self, file_path: Path, folder_path: Path | None, repo_path: Path) -> Skill:
        return Skill(
            file_path=file_path,
            folder_path=folder_path,
            source=LocalSource(scan_path=file_path.parent, repo_path=repo_path),
            format=SkillFormat.HumanFlat if folder_path is None else SkillFormat.Agent,
            source_path=file_path.parent,
        )

    def _flat_skill_file(self) -> SkillFile:
        md = self.flat_dir / "guide.skill.md"
        return SkillFile(path=md, skill=self._skill(md, None, self.flat_dir))

    def _dir_skill_file(self) -> SkillFile:
        md = self.dir_dir / "SKILL.md"
        return SkillFile(path=md, skill=self._skill(md, self.dir_dir, self.repo_root))

    def _path_link(self, skill_file: SkillFile, raw_path: str) -> PathLink:
        return PathLink(
            raw=f"[text]({raw_path})",
            text="text",
            format=MarkdownLinkBuilder,
            start=0,
            end=1,
            skill_file_value=skill_file,
            raw_path=raw_path,
            header_value=None,
            is_image_value=False,
        )

    # ==================================================================
    # Relative raw path
    # Относительный сырой путь
    # ==================================================================

    def test_relative_flat_self(self):
        # EN: A relative link from a flat skill to its own main file must be
        # classified as relative and formatted as ./<file_name>.
        # RU: Относительная ссылка из плоского скилла на его основной файл
        # должна быть относительной и иметь формат ./<имя_файла>.
        link = self._path_link(self._flat_skill_file(), "./guide.skill.md")
        self.assertEqual(link.path_raw.kind, PathKind.relative)
        self.assertEqual(link.path.kind, LinkKind.skill)
        self.assertEqual(link.path.formatted, "./guide.skill.md")

    def test_relative_flat_other(self):
        # EN: A relative link from a flat skill to another file in the same
        # repository folder becomes repo_absolute because flat skills have no
        # skill directory.
        # RU: Относительная ссылка из плоского скилла на другой файл в той же
        # папке репозитория становится repo_absolute, потому что у плоского
        # скилла нет директории скилла.
        link = self._path_link(self._flat_skill_file(), "./other.md")
        self.assertEqual(link.path_raw.kind, PathKind.relative)
        self.assertEqual(link.path.kind, LinkKind.source)
        self.assertEqual(link.path.formatted, "other.md")

    def test_relative_dir_self(self):
        # EN: A relative link from a directory skill to its own main file is
        # classified as relative and points to ./SKILL.md.
        # RU: Относительная ссылка из директорийного скилла на его основной
        # файл является относительной и указывает на ./SKILL.md.
        link = self._path_link(self._dir_skill_file(), "./SKILL.md")
        self.assertEqual(link.path_raw.kind, PathKind.relative)
        self.assertEqual(link.path.kind, LinkKind.skill)
        self.assertEqual(link.path.formatted, "./SKILL.md")

    def test_relative_dir_inside(self):
        # EN: A relative link to a file inside the skill directory stays
        # relative.
        # RU: Относительная ссылка на файл внутри директории скилла остаётся
        # относительной.
        link = self._path_link(self._dir_skill_file(), "./details.md")
        self.assertEqual(link.path.kind, LinkKind.skill)
        self.assertEqual(link.path.formatted, "./details.md")

    def test_relative_dir_sub(self):
        # EN: A relative link to a nested file inside the skill directory stays
        # relative and preserves the sub-path.
        # RU: Относительная ссылка на вложенный файл внутри директории скилла
        # остаётся относительной и сохраняет подпуть.
        link = self._path_link(self._dir_skill_file(), "./sub/nested.md")
        self.assertEqual(link.path.kind, LinkKind.skill)
        self.assertEqual(link.path.formatted, "./sub/nested.md")

    def test_relative_dir_outside_inside_repo(self):
        # EN: A relative link that leaves the skill directory but stays inside
        # the repository becomes repo_absolute.
        # RU: Относительная ссылка, выходящая из директории скилла, но
        # остающаяся внутри репозитория, становится repo_absolute.
        link = self._path_link(self._dir_skill_file(), "../other/SKILL.md")
        self.assertEqual(link.path.kind, LinkKind.source)
        self.assertEqual(link.path.formatted, "other/SKILL.md")

    # ==================================================================
    # Repo-absolute raw path
    # Путь от корня репозитория
    # ==================================================================

    def test_repo_absolute_flat_self(self):
        # EN: A repo-absolute link from a flat skill to its own main file is
        # treated as a self-link and becomes relative.
        # RU: Ссылка от корня репозитория из плоского скилла на его основной
        # файл считается ссылкой на себя и становится относительной.
        link = self._path_link(self._flat_skill_file(), "guide.skill.md")
        self.assertEqual(link.path_raw.kind, PathKind.repo_absolute)
        self.assertEqual(link.path.kind, LinkKind.skill)
        self.assertEqual(link.path.formatted, "./guide.skill.md")

    def test_repo_absolute_flat_other(self):
        # EN: A repo-absolute link from a flat skill to another file in the same
        # folder stays repo_absolute.
        # RU: Ссылка от корня репозитория из плоского скилла на другой файл в
        # той же папке остаётся repo_absolute.
        link = self._path_link(self._flat_skill_file(), "other.md")
        self.assertEqual(link.path_raw.kind, PathKind.repo_absolute)
        self.assertEqual(link.path.kind, LinkKind.source)
        self.assertEqual(link.path.formatted, "other.md")

    def test_repo_absolute_dir_self(self):
        # EN: A repo-absolute link that targets the directory skill's main file
        # becomes relative because the target is the skill file itself.
        # RU: Ссылка от корня репозитория, указывающая на основной файл
        # директорийного скилла, становится относительной, так как цель — сам
        # файл скилла.
        link = self._path_link(self._dir_skill_file(), "dir/SKILL.md")
        self.assertEqual(link.path_raw.kind, PathKind.repo_absolute)
        self.assertEqual(link.path.kind, LinkKind.skill)
        self.assertEqual(link.path.formatted, "./SKILL.md")

    def test_repo_absolute_dir_inside(self):
        # EN: A repo-absolute link to a file inside the skill directory becomes
        # relative.
        # RU: Ссылка от корня репозитория на файл внутри директории скилла
        # становится относительной.
        link = self._path_link(self._dir_skill_file(), "dir/details.md")
        self.assertEqual(link.path.kind, LinkKind.skill)
        self.assertEqual(link.path.formatted, "./details.md")

    def test_repo_absolute_dir_sub(self):
        # EN: A repo-absolute link to a nested file inside the skill directory
        # becomes relative and preserves the sub-path.
        # RU: Ссылка от корня репозитория на вложенный файл внутри директории
        # скилла становится относительной и сохраняет подпуть.
        link = self._path_link(self._dir_skill_file(), "dir/sub/nested.md")
        self.assertEqual(link.path.kind, LinkKind.skill)
        self.assertEqual(link.path.formatted, "./sub/nested.md")

    def test_repo_absolute_dir_outside(self):
        # EN: A repo-absolute link to a file outside the skill directory but
        # inside the repository stays repo_absolute.
        # RU: Ссылка от корня репозитория на файл вне директории скилла, но
        # внутри репозитория, остаётся repo_absolute.
        link = self._path_link(self._dir_skill_file(), "other/SKILL.md")
        self.assertEqual(link.path.kind, LinkKind.source)
        self.assertEqual(link.path.formatted, "other/SKILL.md")

    # ==================================================================
    # OS-absolute raw path
    # Абсолютный путь ОС
    # ==================================================================

    def test_os_absolute_flat_self(self):
        # EN: An OS-absolute raw link that resolves inside the repository root
        # is treated as repo-absolute. If it points to the flat skill's own
        # file, it becomes relative.
        # RU: Абсолютный путь ОС, разрешающийся внутри корня репозитория,
        # считается repo-absolute. Если он указывает на собственный файл
        # плоского скилла, он становится относительным.
        link = self._path_link(
            self._flat_skill_file(), str(self.flat_dir / "guide.skill.md")
        )
        self.assertEqual(link.path_raw.kind, PathKind.os_absolute)
        self.assertEqual(link.path.kind, LinkKind.skill)
        self.assertEqual(link.path.formatted, "./guide.skill.md")

    def test_os_absolute_flat_other(self):
        # EN: An OS-absolute raw link inside the repository root to another file
        # becomes repo_absolute.
        # RU: Абсолютный путь ОС внутри корня репозитория на другой файл
        # становится repo_absolute.
        link = self._path_link(self._flat_skill_file(), str(self.flat_dir / "other.md"))
        self.assertEqual(link.path_raw.kind, PathKind.os_absolute)
        self.assertEqual(link.path.kind, LinkKind.source)
        self.assertEqual(link.path.formatted, "other.md")

    def test_os_absolute_dir_self(self):
        # EN: An OS-absolute raw link inside the repository root to the
        # directory skill's main file becomes relative.
        # RU: Абсолютный путь ОС внутри корня репозитория на основной файл
        # директорийного скилла становится относительным.
        link = self._path_link(
            self._dir_skill_file(), str(self.repo_root / "dir/SKILL.md")
        )
        self.assertEqual(link.path_raw.kind, PathKind.os_absolute)
        self.assertEqual(link.path.kind, LinkKind.skill)
        self.assertEqual(link.path.formatted, "./SKILL.md")

    def test_os_absolute_dir_inside(self):
        # EN: An OS-absolute raw link inside the repository root to a file
        # inside the skill directory becomes relative.
        # RU: Абсолютный путь ОС внутри корня репозитория на файл внутри
        # директории скилла становится относительным.
        link = self._path_link(
            self._dir_skill_file(), str(self.repo_root / "dir/details.md")
        )
        self.assertEqual(link.path.kind, LinkKind.skill)
        self.assertEqual(link.path.formatted, "./details.md")

    def test_os_absolute_dir_outside(self):
        # EN: An OS-absolute raw link inside the repository root to a file
        # outside the skill directory but inside the repository becomes
        # repo_absolute.
        # RU: Абсолютный путь ОС внутри корня репозитория на файл вне
        # директории скилла, но внутри репозитория, становится repo_absolute.
        link = self._path_link(
            self._dir_skill_file(), str(self.repo_root / "other/SKILL.md")
        )
        self.assertEqual(link.path.kind, LinkKind.source)
        self.assertEqual(link.path.formatted, "other/SKILL.md")

    # ==================================================================
    # Outside repository
    # Выход за пределы репозитория
    # ==================================================================

    def test_relative_outside_repo_raises(self):
        # EN: A relative link that resolves outside the repository root must
        # raise ValueError.
        # RU: Относительная ссылка, разрешающаяся за пределами корня
        # репозитория, должна выбрасывать ValueError.
        with self.assertRaises(ValueError):
            self._path_link(self._dir_skill_file(), "../../outside.md")

    def test_os_absolute_outside_repo(self):
        # EN: An OS-absolute raw link that resolves outside the repository root
        # becomes an OS link and records that it is outside the repository.
        # RU: Абсолютный путь ОС, разрешающийся за пределами корня репозитория,
        # становится OS-ссылкой и фиксирует, что он вне репозитория.
        link = self._path_link(self._dir_skill_file(), "/tmp/outside-repo.md")
        self.assertEqual(link.path_raw.kind, PathKind.os_absolute)
        self.assertEqual(link.path.kind, LinkKind.os)
        self.assertFalse(link.path.is_inside_repo)
        self.assertEqual(link.path.repo_path, None)
        self.assertEqual(link.path.formatted, "/tmp/outside-repo.md")

    # ==================================================================
    # Additional cases
    # Дополнительные случаи
    # ==================================================================

    def test_skill_md_fallback(self):
        # EN: A link ending with .skill resolves to an existing .skill.md file.
        # RU: Ссылка, заканчивающаяся на .skill, разрешается в существующий файл .skill.md.
        skill_file = self._dir_skill_file()
        target = self.dir_dir / "a-b-c.skill.md"
        target.write_text("# Skill\n")
        link = self._path_link(skill_file, "./a-b-c.skill")
        self.assertEqual(link.path.kind, LinkKind.skill)
        self.assertEqual(link.path.formatted, "./a-b-c.skill.md")

    def test_missing_file_inside_skill_folder(self):
        # EN: A link to a non-existent file inside the skill folder is still
        # classified as a skill-internal link.
        # RU: Ссылка на несуществующий файл внутри папки скилла всё равно
        # классифицируется как внутри-скилловая.
        link = self._path_link(self._dir_skill_file(), "./missing.md")
        self.assertEqual(link.path.kind, LinkKind.skill)

    def test_web_path_raises(self):
        # EN: Passing a web URI as a raw path to PathLink must raise ValueError
        # because web links are represented by WebLink.
        # RU: Передача веб-URI как сырого пути в PathLink должна выбрасывать
        # ValueError, потому что веб-ссылки представлены классом WebLink.
        with self.assertRaises(ValueError):
            self._path_link(self._flat_skill_file(), "https://example.com")

    def test_target_property(self):
        # EN: PathLink.target returns the formatted resolved path.
        # RU: PathLink.target возвращает отформатированный разрешённый путь.
        link = self._path_link(self._flat_skill_file(), "./guide.skill.md")
        self.assertEqual(link.target, link.path.formatted)

    def test_link_type_property(self):
        # EN: PathLink.link_type returns the PathLink class.
        # RU: PathLink.link_type возвращает класс PathLink.
        link = self._path_link(self._flat_skill_file(), "./guide.skill.md")
        self.assertIs(link.link_type, PathLink)

    def test_exists_property_true(self):
        # EN: PathLink.exists is True when the target file exists.
        # RU: PathLink.exists равен True, когда целевой файл существует.
        link = self._path_link(self._flat_skill_file(), "./guide.skill.md")
        self.assertTrue(link.exists)
        self.assertTrue(link.path.exists)

    def test_exists_property_false(self):
        # EN: PathLink.exists is False when the target file does not exist.
        # RU: PathLink.exists равен False, когда целевой файл не существует.
        link = self._path_link(self._dir_skill_file(), "./missing.md")
        self.assertFalse(link.exists)
        self.assertFalse(link.path.exists)

    def test_has_explicit_md_suffix_true(self):
        # EN: A link with an explicit .md suffix records the flag as True.
        # RU: Ссылка с явным суффиксом .md фиксирует флаг как True.
        link = self._path_link(self._dir_skill_file(), "./details.md")
        self.assertTrue(link.has_explicit_md_suffix)
        self.assertTrue(link.path.has_explicit_md_suffix)

    def test_has_explicit_md_suffix_false(self):
        # EN: A link without an explicit .md suffix records the flag as False,
        # even when the fallback resolves to an existing .md file.
        # RU: Ссылка без явного суффикса .md фиксирует флаг как False, даже
        # если fallback разрешается в существующий .md файл.
        skill_file = self._dir_skill_file()
        target = self.dir_dir / "a-b-c.skill.md"
        target.write_text("# Skill\n")
        link = self._path_link(skill_file, "./a-b-c.skill")
        self.assertFalse(link.has_explicit_md_suffix)
        self.assertTrue(link.exists)

    def test_fragment_only_link_resolves_to_self_in_dir_skill(self):
        # EN: A fragment-only wiki link such as [[#Header]] must resolve to the
        # current skill file so that validation treats it as an internal link.
        # RU: Wiki-ссылка только с фрагментом [[#Заголовок]] должна разрешаться
        # в текущий файл скилла, чтобы валидация считала её внутренней.
        skill_file = self._dir_skill_file()
        link = PathLink(
            raw="[[#Return ConflictResult<T> from the resolver]]",
            text="Return ConflictResult<T> from the resolver",
            format=WikilinkBuilder,
            start=0,
            end=1,
            skill_file_value=skill_file,
            raw_path="",
            header_value="#Return ConflictResult<T> from the resolver",
            is_image_value=False,
        )
        self.assertEqual(link.path_raw.path, "")
        self.assertEqual(link.path_raw.kind, PathKind.repo_absolute)
        self.assertEqual(link.path.kind, LinkKind.skill)
        self.assertEqual(link.path.formatted, "./SKILL.md")
        self.assertEqual(link.path.os_path, skill_file.path)
        self.assertEqual(link.header, "#Return ConflictResult<T> from the resolver")

    def test_fragment_only_link_resolves_to_self_in_flat_skill(self):
        # EN: A fragment-only link in a flat skill resolves to the single skill file.
        # RU: Ссылка только с фрагментом в плоском скилле разрешается в единственный файл.
        skill_file = self._flat_skill_file()
        link = PathLink(
            raw="[[#Return ConflictResult<T> from the resolver]]",
            text="Return ConflictResult<T> from the resolver",
            format=WikilinkBuilder,
            start=0,
            end=1,
            skill_file_value=skill_file,
            raw_path="",
            header_value="#Return ConflictResult<T> from the resolver",
            is_image_value=False,
        )
        self.assertEqual(link.path.formatted, "./guide.skill.md")
        self.assertEqual(link.path.os_path, skill_file.path)


if __name__ == "__main__":
    unittest.main()
