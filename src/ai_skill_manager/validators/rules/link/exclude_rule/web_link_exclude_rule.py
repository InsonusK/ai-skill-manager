"""Exclude rule for external web links.

Правило исключения внешних веб-ссылок.
"""

from typing import List

from .....entities import Skill, WebLink
from .....models import LinkWithContext
from .abs_exclude_rule import absExcludeRule


class WebLinkExcludeRule(absExcludeRule):
    """Skip external URLs — they are always allowed."""

    def should_exclude(self, link: LinkWithContext, skills: List[Skill]) -> bool:
        """Return ``True`` for web links."""
        return isinstance(link.base, WebLink)
