"""Skill format patterns used by discovery strategies.

Паттерны форматов навыков, используемые стратегиями обнаружения.
"""

from .AgentPattern import AgentPattern
from .HumanDirPattern import HumanDirPattern
from .HumanFlatPattern import HumanFlatPattern
from .SkillPattern import SkillPattern

__all__ = [
    "SkillPattern",
    "HumanFlatPattern",
    "HumanDirPattern",
    "AgentPattern",
]
