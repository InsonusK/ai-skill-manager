from pathlib import Path
import re
from ...models import FileContext, LinkLocation
from .abs_link_builder import absLinkBuilder, ContentContext, List,Link

WIKI_LINK_RE = re.compile(r"!?\[\[([^\]]+)\]\]")

class WikilinkBuilder(absLinkBuilder):
    def search(self, content: ContentContext) -> List[Link]:
        links: List[Link] = []
        for match in WIKI_LINK_RE.finditer(content.content):
            links.append(self._build_wiki_link(match, content.file))

    def _build_wiki_link(self, match: re.Match, file: FileContext) -> Link:
        raw = match.group(0)
        inner = match.group(1)

        if "|" in inner:
            left, custom_text = inner.rsplit("|", 1)
        else:
            left = inner
            custom_text = None

        path_clean, fragment = self._split_fragment(left)
        display_text = custom_text if custom_text is not None else Path(
            path_clean).name

        return Link(
            raw=raw,
            path=path_clean,
            text=display_text,
            kind=self._get_kind(path_clean),
            format="wiki",
            context=LinkLocation(
                file=file,
                start=match.start(),
                end=match.end(),
            ),
            header=fragment,
            is_image=self._is_image(raw)
        )
