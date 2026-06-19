"""Link replacement in markdown files.

Finds all links in a file, dispatches each one through the mapper, writes
a copy of the file with updated links, and returns the copy path together
with the list of performed fixes.
"""

import logging
import re
from pathlib import Path
from typing import List, Optional, Tuple

from .base import Context, Link, ReplaceResult
from .map import LinkMapError, LinkMapper

logger = logging.getLogger(__name__)

MD_LINK_RE = re.compile(r'!?\[([^\]]*)\]\(([^\s\)"]*)\)')
WIKI_LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


class LinkReplacer:
    """Replaces links in a markdown file using a mapper."""

    def __init__(self, mapper: Optional[LinkMapper] = None):
        self.mapper = mapper or LinkMapper()

    def replace(self, filepath: Path, context: Context) -> ReplaceResult:
        """Create a copy of ``filepath`` with links updated.

        Args:
            filepath: Path to the markdown file to process.
            context: Adaptation context.

        Returns:
            A ``ReplaceResult`` containing the path to the new file and the
            list of fixes that were performed or recorded.
        """
        content = filepath.read_text(encoding="utf-8")
        links = self._parse_links(content)

        parts: List[str] = []
        last_end = 0
        fixes: List[dict] = []

        for pos, link in links:
            parts.append(content[last_end:pos])

            if self._is_skipped(link):
                parts.append(link.full)
                last_end = pos + len(link.full)
                continue

            try:
                replacement = self.mapper.map(link, context)
                status = "fixed"
                reason: Optional[str] = None
            except (LinkMapError, RuntimeError) as exc:
                replacement = link.full
                status = "broken"
                reason = str(exc)
                logger.warning(
                    "Link %s in %s left unchanged: %s",
                    link.full, filepath, reason
                )

            parts.append(replacement)
            last_end = pos + len(link.full)

            fix: dict = {"file": str(filepath), "old": link.full, "status": status}
            if reason:
                fix["reason"] = reason
            if status == "fixed":
                fix["new"] = replacement
            fixes.append(fix)

        parts.append(content[last_end:])
        new_content = "".join(parts)

        new_path = filepath.with_suffix(filepath.suffix + ".link_update")
        new_path.write_text(new_content, encoding="utf-8")

        return ReplaceResult(new_path=new_path, fixes=fixes)

    def _is_skipped(self, link: Link) -> bool:
        """Return True for links that should be left untouched."""
        if link.kind != "markdown":
            return False
        target = link.target
        return (
            not target
            or target.startswith("#")
            or target.startswith(("http://", "https://", "ftp://", "mailto:"))
        )

    def _parse_links(self, content: str) -> List[Tuple[int, Link]]:
        """Parse all links from content, returning list of (position, Link)."""
        links: List[Tuple[int, Link]] = []

        for match in MD_LINK_RE.finditer(content):
            full = match.group(0)
            text = match.group(1)
            path = match.group(2)
            is_image = full.startswith("!")

            path_clean, fragment = self._split_fragment(path)

            links.append((match.start(), Link(
                full=full,
                kind="markdown",
                text=text,
                target=path_clean,
                fragment=fragment,
                is_image=is_image,
            )))

        for match in WIKI_LINK_RE.finditer(content):
            full = match.group(0)
            inner = match.group(1)

            if "|" in inner:
                left, custom_text = inner.rsplit("|", 1)
            else:
                left = inner
                custom_text = None

            target, fragment = self._split_fragment(left)
            display_text = custom_text if custom_text is not None else Path(target).name

            links.append((match.start(), Link(
                full=full,
                kind="wiki",
                text=display_text,
                target=target,
                fragment=fragment,
                is_image=False,
            )))

        links.sort(key=lambda x: x[0])
        return links

    @staticmethod
    def _split_fragment(path: str) -> Tuple[str, str]:
        """Split a path into path and #fragment parts."""
        if "#" in path:
            path_clean, fragment = path.split("#", 1)
            return path_clean, f"#{fragment}"
        return path, ""
