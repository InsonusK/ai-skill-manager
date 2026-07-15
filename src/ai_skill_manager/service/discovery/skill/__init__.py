"""Skill discovery strategies.

Exports the concrete discovery strategy used to scan local paths and
GitHub repositories for skill definitions.

Стратегии обнаружения навыков.
Экспортирует конкретную стратегию обнаружения, используемую для сканирования
локальных путей и репозиториев GitHub на наличие определений навыков.
"""

from .auto import AutoDiscovery

__all__ = [
    "AutoDiscovery",
]
