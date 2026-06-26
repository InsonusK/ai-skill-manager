"""HumanDir skill pattern.

Паттерн навыка HumanDir.
"""

from pathlib import Path
from typing import Optional

from ....entities import Skill, SkillFormat
from .SkillPattern import absSkillTemplate


class HumanDirPattern(absSkillTemplate):
    """Detects directory skill in human friendly format: 
    
    file ``{skill_name}.skill.md`` inside a directory ``{skill_name}.skill``.

    Обнаруживает директориальные скилов в человеко ориентрованном формате:
    файл ``{skill_name}.skill.md`` внутри директории ``{skill_name}.skill``.
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
    
    @staticmethod
    def __is_directory_name_correct(path:Path)->bool:
        """
        Directory name must end on ``.skill``
        
        Название директории должно заканчиваться на ``.skill``
        """        
        return path.name.endswith(".skill")
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
        
        if not HumanDirPattern.__is_directory_name_correct(path):
            return None
        
        # Expected skill markdown file named after the directory.
        # Ожидаемый skill-файл, названный по имени директории.
        skill_md = path / f"{path.name}.md"
        if skill_md.is_file():
            return Skill(
                file_path=skill_md,
                folder_path=path,
                format=self.skill_format,
                source=self._source,
                source_path=self._source_path
            )
        return None
