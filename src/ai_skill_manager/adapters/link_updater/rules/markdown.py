"""Rule for Markdown links.

Handles relative Markdown links such as ``[text](./relative/path)``.
Absolute Markdown links are not supported and will not be matched.
"""
from ..models import Link
from ..base import LinkContext, format_link, resolve_target
from .absRule import LinkRule

class MarkdawnLinkRule(LinkRule):
    """Adapter for Markdown links.

    Matches links like ``[text](./sub/file.md)``. Relative and absolute
    paths are detected by separate helper methods, but only relative
    Markdown links are currently supported.
    """
    def match(self, link: Link) -> bool:
        if link.kind != "markdown":
            return False
        return self._is_relative(link) or self._is_absolute(link)

    def _is_relative(self, link: Link) -> bool:
        """Return True for links starting with ``./`` or ``../``."""
        return link.target.startswith(("./", "../"))

    def _is_absolute(self, link: Link) -> bool:
        """Return True for absolute repo-root paths.

        Absolute Markdown links are currently not supported, so this
        always returns False.
        """
        return False

    def to_skill_format(self, link: Link, context: LinkContext) -> str:
        if self._is_relative(link):
            return self._apply_relative(link, context)
        if self._is_absolute(link):
            return self._apply_absolute(link, context)
        raise RuntimeError(f"unsupported Markdown link: {link.target}")

    def _apply_relative(self, link: Link, context: LinkContext) -> str:
        """Resolve a relative Markdown link against the current file."""
        source_file = context.target_to_source.get(context.filepath, context.filepath)
        target_file = resolve_target(source_file.parent / link.target, context)
        if not target_file:
            raise RuntimeError(f"target file does not exist: {link.target}")
        return format_link(link, target_file, context)

    def _apply_absolute(self, link: Link, context: LinkContext) -> str:
        """Resolve an absolute Markdown link against the repo root."""
        raise RuntimeError(f"absolute Markdown links are not supported: {link.target}")
