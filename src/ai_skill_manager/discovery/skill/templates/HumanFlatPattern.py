"""HumanFlat skill pattern.

Паттерн навыка HumanFlat.
"""

import logging
from pathlib import Path
from typing import Optional

from ....entities import Skill, SkillFormat
from .SkillPattern import absSkillTemplate

# Module logger / Логгер модуля.
logger = logging.getLogger(__name__)


class HumanFlatPattern(absSkillTemplate):
    """Detects flat skill in human friendly format: a single ``*.skill.md`` file.

    Обнаруживает плоские скилы в человеко ориентрованном формате: один файл ``*.skill.md``.
    """

    def __init__(self, source, source_path):
        """Initialize the HumanFlat pattern.

        Initialize the HumanFlat pattern.

        Инициализировать паттерн HumanFlat.

        Args:
            source: Source metadata for matched skills. /
                Метаданные источника для совпавших навыков.
            source_path: Base source path. / Базовый путь источника.
        """
        super().__init__(source, source_path)

    # Format produced by this pattern. / Формат, производимый этим паттерном.
    skill_format = SkillFormat.HumanFlat

    def match(self, path: Path) -> Optional[Skill]:
        """Match a file ending with ``.skill.md``.

        Match a file ending with ``.skill.md``.

        Сопоставить файл, заканчивающийся на ``.skill.md``.

        Args:
            path: Path to check. / Путь для проверки.

        Returns:
            Flat :class:`Skill` if matched, otherwise ``None``. /
            Плоский :class:`Skill` при совпадении, иначе ``None``.
        """
        if path.is_file() and path.name.endswith(".skill.md"):
            logger.debug("HumanFlat pattern matched: %s", path)
            # Flat skills have no associated folder.
            # У плоских навыков нет связанной директории.
            return Skill(
                file_path=path,
                folder_path=None,
                format=self.skill_format,
                source=self._source,
                source_path=self._source_path
            )
        logger.debug("HumanFlat pattern did not match: %s", path)
        return None
