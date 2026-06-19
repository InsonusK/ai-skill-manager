"""Skill discovery module.

Public API for discovering skills from local directories or GitHub
repositories. Discovery returns ``Skill`` objects and does not handle
sync/copy concerns.

Публичный API для обнаружения навыков из локальных директорий или
репозиториев GitHub. Discovery возвращает объекты ``Skill`` и не
занимается синхронизацией/копированием.
"""

from .api import STRATEGIES, discover
from .models import Source

__all__ = [
    "Source",
    "STRATEGIES",
    "discover",
]
