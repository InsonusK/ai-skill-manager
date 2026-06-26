"""Agent skill pattern.

Паттерн навыка Agent.
"""

from pathlib import Path
from typing import Optional

from ....entities import Skill, SkillFormat
from .SkillPattern import absSkillTemplate


class AgentTemplate(absSkillTemplate):
    """Detects skills in agent format: ``SKILL.md`` inside a directory.

    Обнаруживает навыки в агентском формате: файл ``SKILL.md`` внутри директории.
    """

    def __init__(self, source, source_path):
        """Initialize the Agent pattern.

        Initialize the Agent pattern.

        Инициализировать паттерн Agent.

        Args:
            source: Source metadata for matched skills. /
                Метаданные источника для совпавших навыков.
            source_path: Base source path. / Базовый путь источника.
        """
        super().__init__(source, source_path)

    # Format produced by this pattern. / Формат, производимый этим паттерном.
    skill_format = SkillFormat.Agent

    def match(
        self, path: Path
    ) -> Optional[Skill]:
        """Match a directory containing ``SKILL.md``.

        Match a directory containing ``SKILL.md``.

        Сопоставить директорию, содержащую ``SKILL.md``.

        Args:
            path: Path to check. / Путь для проверки.

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
                source=self._source,
                source_path=self._source_path
            )
        return None
