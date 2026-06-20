"""Models for parsed markdown links."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

from ai_skill_manager.models.skill import Skill


@dataclass(frozen=True)
class LinkLocation:
    """Where a link was found in the source text.

    Attributes:
        filepath: Path to the file containing the link.
        skill: The skill the file belongs to, if known.
        start: Character offset where the link starts in the content.
        end: Character offset where the link ends in the content.
    """

    filepath: Path
    skill: Optional[Skill]
    start: int
    end: int


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
    kind: Literal["markdown", "wiki"]
    context: LinkLocation
    fragment: str = ""
    is_image: bool = False

    @property
    def full(self) -> str:
        """Backward-compatible alias for :attr:`raw`."""
        return self.raw

    @property
    def target(self) -> str:
        """Backward-compatible alias for :attr:`path`."""
        return self.path
