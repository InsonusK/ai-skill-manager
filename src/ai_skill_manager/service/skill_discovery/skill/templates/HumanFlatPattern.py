"""HumanFlat skill pattern.

Паттерн навыка HumanFlat.
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


class HumanFlatPattern(absSkillTemplate):
    """Detects flat skill in human friendly format: a single ``*.skill.md`` file.

    Обнаруживает плоские скилы в человеко ориентрованном формате: один файл ``*.skill.md``.
    """

    @property
    def pattern_description(self) -> str:
        """Return the pattern example for a flat skill file."""
        return "{name}.skill.md"

    def match(self, path: Path) -> Optional[Skill]:
        """Match a file ending with ``.skill.md``.

        Match a file ending with ``.skill.md``.

        Сопоставить файл, заканчивающийся на ``.skill.md``.

        Args:
            path: Path to check. / Путь для проверки.

        Returns:
            Flat :class:`Skill` if matched, otherwise ``None``. /
            Плоский :class:`Skill` при совпадении, иначе ``None``.

        Raises:
            ValueError: If the file matches but has no valid frontmatter
                ``name``. / Если файл совпадает, но в его frontmatter нет
                корректного ``name``.
        """
        if path.is_file() and path.name.endswith(".skill.md"):
            logger.debug("HumanFlat pattern matched: %s", path)
            name = SkillProperty(path).name
            if name is None:
                raise ValueError(f"Skill {path} has no 'name' in frontmatter")
            # Flat skills have no associated folder.
            # У плоских навыков нет связанной директории.
            return Skill(name=name, path=path, kind=SkillKind.flat)
        logger.debug("HumanFlat pattern did not match: %s", path)
        return None
