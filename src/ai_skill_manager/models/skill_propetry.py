from pathlib import Path
from typing import Any, Optional

import yaml


class SkillProperty:
    def __init__(self, skill_path: Path):
        self.__skill_path = skill_path
        self.__property_dict = None
    @property
    def all(self)->dict[str,Any]:
        if self.__property_dict is None:
            self.__property_dict = SkillProperty._parse_frontmatter(self.__skill_path)
        return self.__property_dict
    
    @property
    def name(self)->Optional[str]:
        return self.all.get("name", None)            
        
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
