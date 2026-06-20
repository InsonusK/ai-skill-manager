"""Factory for creating :class:`Link` objects from markdown content."""

import re
from pathlib import Path
from typing import List, Optional, Tuple

from ai_skill_manager.models.skill import Skill

from ..models.Link import Link, LinkLocation


MD_LINK_RE = re.compile(r'!?\[([^\]]*)\]\(([^\s\)"]*)\)')
WIKI_LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


class LinkFactory:
    """Parses markdown content and builds :class:`Link` instances.

    The factory is bound to a concrete file and optional skill. It extracts
    both markdown-style links and wiki-style links, preserving their
    positions in the original content so callers can replace them later.
    """

    def create_links(self, content: str) -> List[Link]:
        """Parse all links from ``content`` and return them in source order."""
        links: List[Link] = []

        for match in MD_LINK_RE.finditer(content):
            links.append(self._build_markdown_link(match))

        for match in WIKI_LINK_RE.finditer(content):
            links.append(self._build_wiki_link(match))

        links.sort(key=lambda link: link.context.start)
        return links

    def _build_markdown_link(self, match: re.Match) -> Link:
        raw = match.group(0)
        text = match.group(1)
        path_raw = match.group(2)
        is_image = raw.startswith("!")

        path_clean, fragment = self._split_fragment(path_raw)

        return Link(
            raw=raw,
            path=path_clean,
            text=text,
            kind="markdown",
            context=LinkLocation(
                filepath=self.filepath,
                skill=self.skill,
                start=match.start(),
                end=match.end(),
            ),
            fragment=fragment,
            is_image=is_image,
        )

    def _build_wiki_link(self, match: re.Match) -> Link:
        raw = match.group(0)
        inner = match.group(1)

        if "|" in inner:
            left, custom_text = inner.rsplit("|", 1)
        else:
            left = inner
            custom_text = None

        path_clean, fragment = self._split_fragment(left)
        display_text = custom_text if custom_text is not None else Path(path_clean).name

        return Link(
            raw=raw,
            path=path_clean,
            text=display_text,
            kind="wiki",
            context=LinkLocation(
                filepath=self.filepath,
                skill=self.skill,
                start=match.start(),
                end=match.end(),
            ),
            fragment=fragment,
            is_image=False,
        )

    @staticmethod
    def _split_fragment(path: str) -> Tuple[str, str]:
        """Split a path into path and ``#fragment`` parts."""
        if "#" in path:
            path_clean, fragment = path.split("#", 1)
            return path_clean, f"#{fragment}"
        return path, ""
