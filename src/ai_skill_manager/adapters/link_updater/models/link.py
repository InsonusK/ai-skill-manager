"""Models for parsed markdown links."""

from dataclasses import dataclass
from typing import Literal, Optional

from .link_location import LinkLocation
from .link_kind import LinkKind
@dataclass(frozen=True)
class Link:
    """Represents a parsed link found in markdown content.

    Attributes:
        raw: The exact link text as it appears in the source.
        path: The link target path without the URL fragment.
        text: The display text of the link.
        kind: Whether the link is a markdown or wiki link.
        context: Where the link was found in the source text.
        fragment: The optional ``#fragment`` part of the link target.
        is_image: ``True`` for image links (``![...](...)``).
    """

    raw: str
    path: str
    text: str
    kind: LinkKind
    format: Literal["markdown", "wiki"]
    context: LinkLocation
    header: Optional[str] = None
    is_image: bool = False

    @property
    def full(self) -> str:
        """Backward-compatible alias for :attr:`raw`."""
        return self.raw

    @property
    def target(self) -> str:
        """Backward-compatible alias for :attr:`path`."""
        return self.path
