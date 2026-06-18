"""Sync command package.

Exposes the API, formatter and CLI entry points for synchronizing skills.
Экспортирует точки входа API, форматёра и CLI для синхронизации навыков.
"""

from .api import DEFAULT_CONFIG, run_sync
from .cli import add_parser, run

__all__ = ["DEFAULT_CONFIG", "add_parser", "run", "run_sync"]
