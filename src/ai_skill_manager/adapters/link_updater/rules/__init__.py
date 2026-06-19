"""Link transformation rules."""

from .absRule import LinkRule
from .markdawn_relative import MarkdawnRelativeRule
from .wikilink_absolute import WikilinkAbsoluteRule
from .wikilink_relative import WikilinkRelativeRule

__all__ = [
    "LinkRule",
    "MarkdawnRelativeRule",
    "WikilinkAbsoluteRule",
    "WikilinkRelativeRule",
]
