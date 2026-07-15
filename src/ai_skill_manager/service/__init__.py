"""High-level services package.

Exports the skill-discovery function reused by the new pipeline's
``SkillDiscovery``/``SkillAtPathFinder``.

Пакет высокоуровневых сервисов.
Экспортирует функцию обнаружения скиллов, переиспользуемую
``SkillDiscovery``/``SkillAtPathFinder`` новой архитектуры.
"""

from .skill_discovery import discover

__all__ = [
    "discover",
]
