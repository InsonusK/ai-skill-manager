"""Factory for creating :class:`Link` objects from markdown content."""
from pathlib import Path
from typing import List

from ....models import Skill
from ..models import FileContext, Link, ContentContext
from .builder import absLinkBuilder, WikilinkBuilder, MarkdownLinkBuilder

DEFAULT_RULES: List[absLinkBuilder] = [WikilinkBuilder(), MarkdownLinkBuilder()]


class LinkFactory:
    """Parses markdown content and builds :class:`Link` instances.

    The factory is bound to a concrete file and optional skill. It extracts
    both markdown-style links and wiki-style links, preserving their
    positions in the original content so callers can replace them later.
    """

    def __init__(self, rules: List[absLinkBuilder] = DEFAULT_RULES):
        self.__search_rules: List[absLinkBuilder] = rules

    def create_links(self, file: FileContext) -> List[Link]:
        """Parse all links from ``file`` and return them in source order."""
        content_context = ContentContext(file)
        links: List[Link] = []

        for rule in self.__search_rules:
            rule_links: List[Link] = rule.search(content_context)
            links.extend(rule_links)

        links.sort(key=lambda link: link.context.start)
        return links

    def create_links_for_skill(self, skill: Skill) -> List[Link]:
        """Parse all links from ``skill`` and its nested markdown files.

        Always parses the skill's own markdown file. When ``skill.is_dir`` is
        ``True``, all ``*.md`` files under ``skill.folder_path`` are also
        parsed recursively.
        """
        files: List[Path] = [skill.file_path]
        if skill.is_dir and skill.folder_path is not None:
            files.extend(sorted(skill.folder_path.rglob("*.md")))

        links: List[Link] = []
        seen: set[Path] = set()
        for file_path in files:
            if file_path in seen:
                continue
            seen.add(file_path)
            links.extend(self.create_links(FileContext(path=file_path, skill=skill)))

        return links

