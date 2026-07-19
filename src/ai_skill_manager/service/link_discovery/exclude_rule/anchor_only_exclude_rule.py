"""Exclude rule for same-document anchor-only links.

Правило исключения ссылок-якорей без пути, указывающих на текущий документ.
"""

from ....models import LinkWithContext
from .abs_exclude_rule import absExcludeRule


class AnchorOnlyExcludeRule(absExcludeRule):
    """Skip links like ``[TOC](#section)`` that carry no path, only a fragment.

    Without this rule, an empty ``raw_path`` is classified as repo-absolute
    and resolves to the repository root itself, which then gets copied
    whole as an "external file".

    Без этого правила пустой ``raw_path`` классифицируется как
    repo-absolute и разрешается в сам корень репозитория, который затем
    целиком копируется как "внешний файл".
    """

    def should_exclude(self, link: LinkWithContext) -> bool:
        """Return ``True`` for links whose path is empty (anchor-only)."""
        return link.base.raw_path == ""
