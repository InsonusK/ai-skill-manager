"""Discover command package.

Exposes the CLI entry point and formatter for discovering skills.

Экспортирует точку входа CLI и форматёр для обнаружения навыков.
"""

from .cli import DEFAULT_CONFIG, DEFAULT_TARGET, add_parser, run
from .formatter import format_skills

__all__ = [
    "DEFAULT_CONFIG",
    "DEFAULT_TARGET",
    "add_parser",
    "format_skills",
    "run",
]
