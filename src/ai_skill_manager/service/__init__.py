"""High-level services package.

Exports orchestration functions that combine discovery and synchronization
of skills.

Пакет высокоуровневых сервисов.
Экспортирует функции оркестрации, объединяющие обнаружение и синхронизацию
навыков.
"""

from .discover import discover
from .sync import remove_orphans, run_sync

__all__ = [
    "discover",
    "remove_orphans",
    "run_sync",
]
