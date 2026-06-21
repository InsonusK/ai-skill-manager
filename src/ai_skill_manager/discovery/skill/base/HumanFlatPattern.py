"""HumanFlat skill pattern.

Паттерн навыка HumanFlat.
"""

from pathlib import Path
from typing import Optional

from ....entities import Skill, SkillFormat
from .SkillPattern import SkillPattern


class HumanFlatPattern(SkillPattern):
    """Detects flat human skills: a single ``*.skill.md`` file.

    Обнаруживает плоские человеческие навыки: один файл ``*.skill.md``.
    """
    def __init__(self, source, source_path):
        super().__init__(source, source_path)
        
    # Format produced by this pattern. / Формат, производимый этим паттерном.
    skill_format = SkillFormat.HumanFlat

    def match(self, path: Path) -> Optional[Skill]:
        """Match a file ending with ``.skill.md``.

        Сопоставить файл, заканчивающийся на ``.skill.md``.

        Args:
            path: Path to check. / Путь для проверки.

        Returns:
            Flat :class:`Skill` if matched, otherwise ``None``. /
            Плоский :class:`Skill` при совпадении, иначе ``None``.
        """
        if path.is_file() and path.name.endswith(".skill.md"):
            # Flat skills have no associated folder.
            # У плоских навыков нет связанной директории.
            return Skill(
                file_path=path,
                folder_path=None,
                format=self.skill_format,
                source=self._source,
                source_path=self._source_path
            )
        return None
