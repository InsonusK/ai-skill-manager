"""Factory for creating :class:`Link` objects from markdown content."""
from typing import List
from ....entities.link import Link
from .builder import absLinkBuilder, WikilinkBuilder, MarkdownLinkBuilder

LINK_SEARCH_RULES: List[absLinkBuilder] = [
    WikilinkBuilder(), MarkdownLinkBuilder()]


def search_links_in_content(content: str) -> List[Link]:
    """Parse all links from ``file`` and return them in source order."""
    links: List[Link] = []

    for rule in LINK_SEARCH_RULES:
        rule_links: List[Link] = rule.search(content)
        links.extend(rule_links)

    links.sort(key=lambda link: link.start)
    return links
