from .file_context import FileContext
from dataclasses import dataclass


@dataclass(frozen=True)
class LinkLocation:
    """Where a link was found in the source text.

    Attributes:
        filepath: Path to the file containing the link.
        skill: The skill the file belongs to, if known.
        start: Character offset where the link starts in the content.
        end: Character offset where the link ends in the content.
    """

    file:FileContext
    start: int
    end: int