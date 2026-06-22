"""HumanDir skill pattern.

Паттерн навыка HumanDir.
"""

from pathlib import Path
from typing import Optional

from ....entities import Skill, SkillFormat
from .SkillPattern import SkillPattern


class HumanDirPattern(SkillPattern):
    """Detects directory human skills: ``{dir_name}.skill.md`` inside a directory.

    Detects directory human skills: ``{dir_name}.skill.md`` inside a directory.

    Обнаруживает директориальные человеческие навыки:
    файл ``{dir_name}.skill.md`` внутри директории.
    """

    def __init__(self, source, source_path):
        """Initialize the HumanDir pattern.

        Initialize the HumanDir pattern.

        Инициализировать паттерн HumanDir.

        Args:
            source: Source metadata for matched skills. /
                Метаданные источника для совпавших навыков.
            source_path: Base source path. / Базовый путь источника.
        """
        super().__init__(source, source_path)

    # Format produced by this pattern. / Формат, производимый этим паттерном.
    skill_format = SkillFormat.HumanDir

    def match(
        self, path: Path
    ) -> Optional[Skill]:
        """Match a directory containing ``{dir_name}.skill.md``.

        Match a directory containing ``{dir_name}.skill.md``.

        Сопоставить директорию, содержащую ``{dir_name}.skill.md``.

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

        # Expected skill markdown file named after the directory.
        # Ожидаемый skill-файл, названный по имени директории.
        skill_md = path / f"{path.name}.skill.md"
        if skill_md.is_file():
            return Skill(
                file_path=skill_md,
                folder_path=path,
                format=self.skill_format,
                source=self._source,
                source_path=self._source_path
            )
        return None
