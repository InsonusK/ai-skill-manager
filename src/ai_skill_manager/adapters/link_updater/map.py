"""Link mapping dispatcher.

Selects exactly one matching rule for a link and applies it.
"""

from typing import List, Optional

from .models.Link import Link

from .base import LinkContext
from .rules import LinkRule, MarkdawnRelativeRule, WikilinkAbsoluteRule, WikilinkRelativeRule


class LinkMapError(Exception):
    """Raised when a link cannot be mapped to exactly one rule."""

    pass


class LinkMapper:
    """Dispatches a link to the single matching transformation rule."""

    def __init__(self, rules: Optional[List[LinkRule]] = None):
        self.rules = rules or [
            WikilinkAbsoluteRule(),
            WikilinkRelativeRule(),
            MarkdawnRelativeRule(),
        ]

    def map(self, link: Link, context: LinkContext) -> str:
        """Apply the single matching rule to ``link``.

        Args:
            link: The parsed link to adapt.
            context: Link adaptation context.

        Returns:
            The replacement link string.

        Raises:
            LinkMapError: If zero or multiple rules match the link.
            RuntimeError: If the matched rule cannot resolve the target file.
        """
        matched = [rule for rule in self.rules if rule.match(link)]

        if len(matched) == 0:
            raise LinkMapError(f"no matching rule for link: {link.full}")

        if len(matched) > 1:
            names = ", ".join(rule.__class__.__name__ for rule in matched)
            raise LinkMapError(
                f"ambiguous link matched multiple rules ({names}): {link.full}"
            )

        return matched[0].apply(link, context)
