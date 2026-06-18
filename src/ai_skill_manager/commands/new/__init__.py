"""New skill command package.

Exposes the API, formatter and CLI entry points for creating skills.
Экспортирует точки входа API, форматёра и CLI для создания навыков.
"""

from .api import SKILL_TEMPLATE, create_skill
from .cli import add_parser, run

__all__ = ["SKILL_TEMPLATE", "add_parser", "create_skill", "run"]
