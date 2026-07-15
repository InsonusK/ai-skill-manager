"""Skill discovery strategies.

Exports the concrete discovery strategies used to scan local paths and
GitHub repositories for skill definitions.

Стратегии обнаружения навыков.
Экспортирует конкретные стратегии обнаружения, используемые для сканирования
локальных путей и репозиториев GitHub на наличие определений навыков.
"""

from .auto import AutoDiscovery
from .abs_discovery_strategy import absDiscoveryStrategy

__all__ = [
    "AutoDiscovery",
    "absDiscoveryStrategy",
]
