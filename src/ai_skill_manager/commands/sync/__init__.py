"""Sync command package.

Exposes the API, formatter and CLI entry points for synchronizing skills.

Экспортирует точки входа API, форматёра и CLI для синхронизации навыков.
"""

from .api import DEFAULT_CONFIG, run_sync
from .cli import add_parser, run
from .formatter import format_sync_result

__all__ = ["DEFAULT_CONFIG", "add_parser", "format_sync_result", "run", "run_sync"]
