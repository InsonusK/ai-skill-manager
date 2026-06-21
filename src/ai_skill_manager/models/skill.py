from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

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

    _headers: Dict[str,Any] = field(init=False, default=None)

    @property
    def headers(self)->Dict[str,Any]:
        if self._headers is None:
            headers = self._parse_frontmatter(self.file_path)
            object.__setattr__(self, "_headers", headers)
        return self._headers
    
    def is_flat(self) -> bool:
        return self.folder_path is None

    @property
    def name(self) -> Optional[str]:
        name = self.headers.get("name")
        if name is None or not isinstance(name, str):
            return None
        return name
    
    @staticmethod
    def _parse_frontmatter(file_path: Path) -> dict[str, Any] | None:
        """
        EN: Parse YAML frontmatter from a markdown file.
            Returns the parsed YAML dict, or None if no frontmatter found.
        RU: Распарсить YAML frontmatter из markdown-файла.
            Вернуть распарсенный YAML dict или None, если frontmatter не найден.
        """
        content = file_path.read_text(encoding="utf-8")
        if not content.startswith("---"):
            return None

        # EN: Find the closing --- after the opening one.
        # RU: Найти закрывающий --- после открывающего.
        rest = content[3:]
        end_idx = rest.find("---")
        if end_idx == -1:
            return None

        frontmatter_text = rest[:end_idx].strip()
        if not frontmatter_text:
            return None

        try:
            return yaml.safe_load(frontmatter_text) or {}
        except yaml.YAMLError:
            raise ValueError(f"Failed to parse YAML frontmatter in {file_path}")
