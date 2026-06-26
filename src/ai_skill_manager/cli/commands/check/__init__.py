"""Check command package.

Exposes the CLI entry point and formatter for discovering and validating
skills.

Экспортирует точку входа CLI и форматёр для обнаружения и проверки навыков.
"""

from .cli import DEFAULT_CONFIG, add_parser, run
from .formatter import print_skills

__all__ = [
    "DEFAULT_CONFIG",
    "add_parser",
    "print_skills",
    "run",
]
