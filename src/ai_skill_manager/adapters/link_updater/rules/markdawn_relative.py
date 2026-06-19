"""Rule for relative Markdown links: [text](./relative/path)."""

from pathlib import Path

from ..base import Context, Link, format_link, resolve_target
from .absRule import LinkRule


class MarkdawnRelativeRule(LinkRule):
    """Adapter for Markdown links with relative paths from the current file.

    Matches links like ``[text](./sub/file.md)``.
    """

    def match(self, link: Link) -> bool:
        if link.kind != "markdown":
            return False
        return link.target.startswith("./")

    def apply(self, link: Link, context: Context) -> str:
        source_file = context.target_to_source.get(context.filepath, context.filepath)
        target_file = resolve_target(source_file.parent / link.target, context)
        if not target_file:
            raise RuntimeError(f"target file does not exist: {link.target}")
        return format_link(link, target_file, context)
