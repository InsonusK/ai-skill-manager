import re
from typing import List

from ...models import FileContext, Link, LinkLocation
from .abs_link_builder import ContentContext, absLinkBuilder

MD_LINK_RE = re.compile(r'!?\[([^\]]*)\]\(([^\s\)"]*)\)')


class MarkdownLinkBuilder(absLinkBuilder):
    """Builds :class:`Link` objects from Markdown-style references."""

    def search(self, content: ContentContext) -> List[Link]:
        links: List[Link] = []
        for match in MD_LINK_RE.finditer(content.content):
            links.append(self._build_markdown_link(match, content.file))
        return links

    def _build_markdown_link(self, match: re.Match, file: FileContext) -> Link:
        raw: str = match.group(0)
        text = match.group(1)
        path_raw = match.group(2)
        path_clean, header = self._split_fragment(path_raw)

        return Link(
            raw=raw,
            path=path_clean,
            text=text,
            kind=self._get_kind(path_clean),
            format="markdown",
            context=LinkLocation(
                file=file,
                start=match.start(),
                end=match.end(),
            ),
            header=header,
            is_image=self._is_image(raw),
        )
