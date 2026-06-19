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