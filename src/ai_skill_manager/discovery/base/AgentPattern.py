"""Agent skill pattern.

Паттерн навыка Agent.
"""

from pathlib import Path
from typing import Optional

from ...models import Skill, SkillFormat, Source
from .SkillPattern import SkillPattern


class AgentPattern(SkillPattern):
    """Detects agent skills: ``SKILL.md`` inside a directory.

    Обнаруживает навыки агента: файл ``SKILL.md`` внутри директории.
    """

    # Format produced by this pattern. / Формат, производимый этим паттерном.
    skill_format = SkillFormat.Agent

    def match(
        self, path: Path, source: Source
    ) -> Optional[Skill]:
        """Match a directory containing ``SKILL.md``.

        Сопоставить директорию, содержащую ``SKILL.md``.

        Args:
            path: Path to check. / Путь для проверки.
            source: Source metadata to attach to the skill. /
                Метаданные источника для навыка.

        Returns:
            Directory :class:`Skill` if matched, otherwise ``None``. /
            Директориальный :class:`Skill` при совпадении, иначе ``None``.
        """
        if not path.is_dir():
            # This pattern only applies to directories.
            # Этот паттерн применяется только к директориям.
            return None

        # Agent skills use a fixed SKILL.md marker.
        # Навыки агента используют фиксированный маркер SKILL.md.
        skill_md = path / "SKILL.md"
        if skill_md.is_file():
            return Skill(
                file_path=skill_md,
                folder_path=path,
                format=self.skill_format,
                source=source,
            )
        return None
