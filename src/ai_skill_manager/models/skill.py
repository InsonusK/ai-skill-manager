from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from .skill_format import SkillFormat
from .source import Source


@dataclass(frozen=True)
class Skill:
    """Represents a discovered skill on disk.

    Представляет обнаруженный навык на диске.
    """

    file_path: Path
    folder_path: Path | None
    source: Source
    format: SkillFormat  # Required skill format. / Обязательный формат навыка.

    def is_flat(self) -> bool:
        return self.folder_path is None

    @property
    def name(self) -> Optional[str]:
        """Read the ``name`` property from the SKILL.md YAML frontmatter.

        Returns ``None`` if frontmatter is missing or the ``name`` key is
        absent. No fallback is applied; a future validator will enforce
        correct skill metadata.

        Возвращает свойство ``name`` из YAML frontmatter файла SKILL.md.
        Возвращает ``None``, если frontmatter отсутствует или в нём нет
        ключа ``name``. Fallback не применяется; корректность метаданных
        навыка будет проверяться отдельным валидатором.
        """
        if not self.file_path.exists():
            return None

        try:
            content = self.file_path.read_text(encoding="utf-8")
        except Exception:
            return None

        if not content.startswith("---"):
            return None

        end = content.find("\n---", 3)
        if end == -1:
            end = content.find("\r\n---", 3)
        if end == -1:
            return None

        try:
            frontmatter = yaml.safe_load(content[3:end])
        except Exception:
            return None

        if not isinstance(frontmatter, dict):
            return None

        name = frontmatter.get("name")
        if name is None or not isinstance(name, str):
            return None

        return name
