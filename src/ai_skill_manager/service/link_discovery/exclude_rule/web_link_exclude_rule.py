"""Exclude rule for external web links.

Правило исключения внешних веб-ссылок.
"""

from ....models import LinkWithContext
from ....tools.link_path import is_http_link
from .abs_exclude_rule import absExcludeRule


class WebLinkExcludeRule(absExcludeRule):
    """Skip external URLs — they are always allowed."""

    def should_exclude(self, link: LinkWithContext) -> bool:
        """Return ``True`` for web links."""
        return is_http_link(link.base.raw_path)
