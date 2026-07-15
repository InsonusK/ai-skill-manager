"""HumanDir skill pattern.

Паттерн навыка HumanDir.
"""

import logging
from pathlib import Path
from typing import Optional

from .....entities.skill_v2 import Skill
from .....entities.skill_kind import SkillKind
from .....entities.skill_propetry import SkillProperty
from .SkillPattern import absSkillTemplate

# Module logger / Логгер модуля.
logger = logging.getLogger(__name__)


class HumanDirPattern(absSkillTemplate):
    """Detects directory skill in human friendly format:

    file ``{skill_name}.skill.md`` inside a directory ``{skill_name}.skill``.

    Обнаруживает директориальные скилов в человеко ориентрованном формате:
    файл ``{skill_name}.skill.md`` внутри директории ``{skill_name}.skill``.
    """

    @property
    def pattern_description(self) -> str:
        """Return the pattern example for a human directory skill."""
        return "{name}.skill/{name}.skill.md"

    @staticmethod
    def __is_directory_name_correct(path: Path) -> bool:
        """
        Directory name must end on ``.skill``

        Название директории должно заканчиваться на ``.skill``
        """
        return path.name.endswith(".skill")

    def match(self, path: Path) -> Optional[Skill]:
        """Match a directory containing ``{dir_name}.skill.md``.

        Match a directory containing ``{dir_name}.skill.md``.

        Сопоставить директорию, содержащую ``{dir_name}.skill.md``.

        Args:
            path: Path to check. / Путь для проверки.

        Returns:
            Directory :class:`Skill` if matched, otherwise ``None``. /
            Директориальный :class:`Skill` при совпадении, иначе ``None``.

        Raises:
            ValueError: If the directory matches but its main file's
                frontmatter is missing a valid ``name``. / Если директория
                совпадает, но во frontmatter её основного файла нет
                корректного ``name``.
        """
        if not path.is_dir():
            # This pattern only applies to directories.
            # Этот паттерн применяется только к директориям.
            logger.debug("HumanDir pattern skipped (not a directory): %s", path)
            return None

        if not HumanDirPattern.__is_directory_name_correct(path):
            logger.debug("HumanDir pattern skipped (directory name does not end with .skill): %s", path)
            return None

        # Expected skill markdown file named after the directory.
        # Ожидаемый skill-файл, названный по имени директории.
        skill_md = path / f"{path.name}.md"
        if skill_md.is_file():
            logger.debug("HumanDir pattern matched: %s -> %s", path, skill_md)
            name = SkillProperty(skill_md).name
            if name is None:
                raise ValueError(f"Skill {skill_md} has no 'name' in frontmatter")
            return Skill(
                name=name,
                path=path,
                kind=SkillKind.dir,
                main_file_relative_path=skill_md.relative_to(path),
            )
        logger.debug("HumanDir pattern did not match (missing %s): %s", skill_md, path)
        return None
