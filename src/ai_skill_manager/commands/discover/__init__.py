"""Discover command package.

Exposes the API, formatter and CLI entry points for discovering skills.
Экспортирует точки входа API, форматёра и CLI для обнаружения навыков.
"""

from .api import (
    DEFAULT_CONFIG,
    DEFAULT_TARGET,
    discover_from_config,
    discover_single_source,
    resolve_target,
)
from .cli import add_parser, run
from .formatter import format_mappings

__all__ = [
    "DEFAULT_CONFIG",
    "DEFAULT_TARGET",
    "add_parser",
    "discover_from_config",
    "discover_single_source",
    "format_mappings",
    "resolve_target",
    "run",
]
