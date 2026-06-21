import re
from typing import List
from .....entities.link import Link
from .abs_link_builder import absLinkBuilder

MD_LINK_RE = re.compile(r'!?\[([^\]]*)\]\(([^\s\)"]*)\)')


class MarkdownLinkBuilder(absLinkBuilder):
    """Builds :class:`Link` objects from Markdown-style references."""

    def search(self, content: str) -> List[Link]:
        """Parse all Markdown-style links from ``content``."""
        links: List[Link] = []
        for match in MD_LINK_RE.finditer(content):
            links.append(self._build_markdown_link(match))
        return links

    def _build_markdown_link(self, match: re.Match) -> Link:
        raw: str = match.group(0)
        text = match.group(1)
        path_raw = match.group(2)
        path_clean, header = self._split_fragment(path_raw)
        start = match.start()
        end = match.end()

        return Link(
            raw=raw,
            path=path_clean,
            text=text,
            kind=self._get_kind(path_clean),
            format="markdown",
            start=start,
            end=end,
            header=header or None,
            is_image=self._is_image(raw),
        )
