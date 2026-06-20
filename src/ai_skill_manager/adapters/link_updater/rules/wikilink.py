"""Rule for wiki links.

Handles both relative wikilinks like ``[[./relative/path|text]]`` and
absolute wikilinks like ``[[skills/foo/SKILL.md|text]]``.
"""
from ..models.link import Link
from ..base import LinkContext, format_link, resolve_target
from .absRule import LinkRule

class WikilinkRule(LinkRule):
    """Adapter for wiki links.

    Matches relative links like ``[[./sub/file.md|text]]`` and absolute
    links like ``[[skills/foo/SKILL.md|text]]``. Plain file-name wikilinks
    without ``/`` are intentionally not matched and are treated as
    forbidden by the mapper.
    """

    def to_skill_format(self, link: Link) -> str:
        if self._is_relative(link):
            return self._apply_relative(link, context)
        if self._is_absolute(link):
            return self._apply_absolute(link, context)
        raise RuntimeError(f"unsupported wiki link: {link.target}")

    def _apply_relative(self, link: Link, context: LinkContext) -> str:
        """Resolve a relative wiki link against the current file."""
        source_file = context.target_to_source.get(context.filepath, context.filepath)
        target_file = resolve_target(source_file.parent / link.target, context)
        if not target_file:
            raise RuntimeError(f"target file does not exist: {link.target}")
        return format_link(link, target_file, context)

    def _apply_absolute(self, link: Link, context: LinkContext) -> str:
        """Resolve an absolute wiki link against the repo root."""
        target_file = resolve_target(context.repo_root / link.target, context)
        if not target_file:
            raise RuntimeError(f"target file does not exist: {link.target}")
        return format_link(link, target_file, context)
