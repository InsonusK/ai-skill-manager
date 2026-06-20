"""Rule for relative wikilinks: [[./relative/path|text]]."""

from pathlib import Path

from ..models.Link import Link

from ..base import LinkContext, format_link, resolve_target
from .absRule import LinkRule


class WikilinkRelativeRule(LinkRule):
    """Adapter for wiki links with relative paths from the current file.

    Matches links like ``[[./sub/file.md|text]]``.
    """

    def match(self, link: Link) -> bool:
        if link.kind != "wiki":
            return False
        return link.target.startswith(("./", "../"))

    def apply(self, link: Link, context: LinkContext) -> str:
        source_file = context.target_to_source.get(context.filepath, context.filepath)
        target_file = resolve_target(source_file.parent / link.target, context)
        if not target_file:
            raise RuntimeError(f"target file does not exist: {link.target}")
        return format_link(link, target_file, context)
