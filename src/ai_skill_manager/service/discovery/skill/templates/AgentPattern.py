"""Agent skill pattern.

Паттерн навыка Agent.
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


class AgentTemplate(absSkillTemplate):
    """Detects skills in agent format: ``SKILL.md`` inside a directory.

    Обнаруживает навыки в агентском формате: файл ``SKILL.md`` внутри директории.
    """

    @property
    def pattern_description(self) -> str:
        """Return the pattern example for an agent skill directory."""
        return "{name}/SKILL.md"

    def match(self, path: Path) -> Optional[Skill]:
        """Match a directory containing ``SKILL.md``.

        Match a directory containing ``SKILL.md``.

        Сопоставить директорию, содержащую ``SKILL.md``.

        Args:
            path: Path to check. / Путь для проверки.

        Returns:
            Directory :class:`Skill` if matched, otherwise ``None``. /
            Директориальный :class:`Skill` при совпадении, иначе ``None``.

        Raises:
            ValueError: If the directory matches but ``SKILL.md``'s
                frontmatter is missing a valid ``name``. / Если директория
                совпадает, но во frontmatter ``SKILL.md`` нет корректного
                ``name``.
        """
        if not path.is_dir():
            # This pattern only applies to directories.
            # Этот паттерн применяется только к директориям.
            logger.debug("Agent pattern skipped (not a directory): %s", path)
            return None

        # Agent skills use a fixed SKILL.md marker.
        # Навыки агента используют фиксированный маркер SKILL.md.
        skill_md = path / "SKILL.md"
        if skill_md.is_file():
            logger.debug("Agent pattern matched: %s -> %s", path, skill_md)
            name = SkillProperty(skill_md).name
            if name is None:
                raise ValueError(f"Skill {skill_md} has no 'name' in frontmatter")
            return Skill(
                name=name,
                path=path,
                kind=SkillKind.dir,
                main_file_relative_path=skill_md.relative_to(path),
            )
        logger.debug("Agent pattern did not match (missing %s): %s", skill_md, path)
        return None
