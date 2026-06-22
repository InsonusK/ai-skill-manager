"""New skill command package.

Exposes the API, formatter and CLI entry points for creating skills.

Экспортирует точки входа API, форматёра и CLI для создания навыков.
"""

from .api import SKILL_TEMPLATE, SkillType, SkillExistsError, create_skill
from .cli import add_parser, run
from .formatter import format_created

__all__ = [
    "SKILL_TEMPLATE",
    "SkillType",
    "SkillExistsError",
    "add_parser",
    "create_skill",
    "format_created",
    "run",
]
