"""Rule for absolute wikilinks: [[absolute/path|text]]."""

from pathlib import Path

from ..models.Link import Link

from ..base import LinkContext, format_link, resolve_target
from .absRule import LinkRule


class WikilinkAbsoluteRule(LinkRule):
    """Adapter for wiki links with absolute paths from the repo root.

    Matches links like ``[[skills/foo/SKILL.md|text]]``. Plain file-name
    wikilinks without ``/`` are intentionally not matched and are treated
    as forbidden by the mapper.
    """

    def match(self, link: Link) -> bool:
        if link.kind != "wiki":
            return False
        target = link.target
        return "/" in target and not target.startswith(("./", "../"))

    def apply(self, link: Link, context: LinkContext) -> str:
        target_file = resolve_target(context.repo_root / link.target, context)
        if not target_file:
            raise RuntimeError(f"target file does not exist: {link.target}")
        return format_link(link, target_file, context)
