"""Link location model.

Модель расположения ссылки.
"""

from dataclasses import dataclass
from pathlib import Path
from ..entities import SkillFile, Skill


@dataclass(frozen=True)
class LinkLocation:
    """Where a link was found in the source text.

    Где ссылка была найдена в исходном тексте.

    Attributes:
        file: The file context for the file containing the link.
            Файловый контекст файла, содержащего ссылку.
        skill: The skill that owns the file.
            Навык, которому принадлежит файл.
    """

    file: SkillFile
    skill: Skill

    @property
    def filepath(self) -> Path:
        """Backward-compatible alias for :attr:`file.path`.

        Обратно совместимый псевдоним для :attr:`file.path`.
        """
        return self.file.path

    def __post_init__(self):
        """Validate that the file belongs to the skill exactly once.

        Проверяет, что файл принадлежит навыку ровно один раз.
        """
        # EN: Find all skill files matching the provided file context.
        # RU: Находим все файлы навыка, соответствующие переданному файловому контексту.
        skill_files = [file for file in self.skill.files if file == self.file]

        # EN: The file must be present in the skill.
        # RU: Файл должен присутствовать в навыке.
        assert len(skill_files) > 0, f"File {self.file.path} doesn't find in files of skill {self.skill.file_path}"

        # EN: The file must be unique within the skill.
        # RU: Файл должен быть уникальным внутри навыка.
        assert len(skill_files) == 1, f"File {self.file.path} has more than 1 candidate in files of skill {self.skill.file_path}"
