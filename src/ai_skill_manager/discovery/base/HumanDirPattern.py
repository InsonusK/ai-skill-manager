"""HumanDir skill pattern.

Паттерн навыка HumanDir.
"""

from pathlib import Path
from typing import Optional

from ...models import Skill, SkillFormat, Source
from .SkillPattern import SkillPattern


class HumanDirPattern(SkillPattern):
    """Detects directory human skills: ``{dir_name}.skill.md`` inside a directory.

    Обнаруживает директориальные человеческие навыки:
    файл ``{dir_name}.skill.md`` внутри директории.
    """

    # Format produced by this pattern. / Формат, производимый этим паттерном.
    skill_format = SkillFormat.HumanDir

    def match(
        self, path: Path, source: Source
    ) -> Optional[Skill]:
        """Match a directory containing ``{dir_name}.skill.md``.

        Сопоставить директорию, содержащую ``{dir_name}.skill.md``.

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

        # Expected skill markdown file named after the directory.
        # Ожидаемый skill-файл, названный по имени директории.
        skill_md = path / f"{path.name}.skill.md"
        if skill_md.is_file():
            return Skill(
                file_path=skill_md,
                folder_path=path,
                format=self.skill_format,
                source=source,
            )
        return None
