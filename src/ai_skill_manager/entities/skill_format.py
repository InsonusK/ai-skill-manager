from __future__ import annotations
from enum import Enum


class SkillFormat(Enum):
    Agent = "AgentSkill"
    """
    Формат AI агента
    - Отдельная директория со скилом
    - Основной файл SKILL.md
    - Название скила = название директории
    """
    HumanFlat = "HumanFlatSkill"
    """
    Плоский (одно файловый скилл)
    - Один файл с названием {skill name}.skill.md
    - Название скила = {skill name}
    """
    HumanDir = "HumanDirSkill"
    """
    Директория со скилом
    - Отдельная директория со скилом
    - Основной файл {skill name}.skill.md
    - Название директории {skill name}.skill
    - Название скила = {skill name}
    """
    
    @property
    def is_flat(self)->bool:
        return self == SkillFormat.HumanFlat
    @property
    def is_dir(self)->bool:
        return not self.is_flat