from dataclasses import dataclass
from pathlib import Path
from .file_context import FileContext,Skill


@dataclass(frozen=True)
class LinkLocation:
    """Where a link was found in the source text.

    Attributes:
        file: The file context for the file containing the link.
        start: Character offset where the link starts in the content.
        end: Character offset where the link ends in the content.
    """

    file: FileContext
    start: int
    end: int

    @property
    def filepath(self) -> Path:
        """Backward-compatible alias for :attr:`file.path`."""
        return self.file.path

    @property
    def skill(self) -> Skill:
        """Backward-compatible alias for :attr:`file.skill`."""
        return self.file.skill
