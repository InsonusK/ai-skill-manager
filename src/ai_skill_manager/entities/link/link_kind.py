"""Link and path kinds.

Типы ссылок и путей.
"""

from enum import Enum


class LinkKind(Enum):
    """Where a resolved link points.

    Куда разрешённая ссылка ведёт.
    """

    skill = "skill"
    """Inside the owning skill (or its directory). / Внутри своего скилла (или директории скилла)."""

    source = "source"
    """Inside the repository but outside the skill. / Внутри репозитория, но вне скилла."""

    external = "external"
    """Outside the repository (web, mailto, etc.). / Вне репозитория (web, mailto и т.д.)."""
