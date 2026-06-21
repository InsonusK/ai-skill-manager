import re
from pathlib import Path
from typing import List

from .....models.link import Link
from .abs_link_builder import absLinkBuilder

WIKI_LINK_RE = re.compile(r"!?\[\[([^\]]+)\]\]")


class WikilinkBuilder(absLinkBuilder):
    """Builds :class:`Link` objects from wiki-style references."""

    def search(self, content: str) -> List[Link]:
        """Parse all wiki-style links from ``content``."""
        links: List[Link] = []
        for match in WIKI_LINK_RE.finditer(content):
            links.append(self._build_wiki_link(match))
        return links

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
        start = match.start()
        end = match.end()

        return Link(
            raw=raw,
            path=path_clean,
            text=display_text,
            kind=self._get_kind(path_clean),
            format="wiki",
            start=start,
            end=end,
            header=fragment or None,
            is_image=self._is_image(raw),
        )