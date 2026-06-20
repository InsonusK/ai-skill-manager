from dataclasses import dataclass, field

from .file_context import FileContext


@dataclass(frozen=True)
class ContentContext:
    """Carries file content together with its file context."""

    file: FileContext
    content: str = field(init=False)

    def __post_init__(self):
        # Обход frozen через object.__setattr__
        object.__setattr__(self, "content", self._read_content(self.file))

    @staticmethod
    def _read_content(file: FileContext) -> str:
        """Return the file content, reading from disk when not provided."""
        if file.content is not None:
            return file.content
        return file.path.read_text(encoding="utf-8")
