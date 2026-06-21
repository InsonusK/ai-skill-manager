"""Factory for creating :class:`Link` objects from markdown content."""
from typing import List
from ..models import FileContext,Link,ContentContext
from .builder import absLinkBuilder,WikilinkBuilder,MarkdownLinkBuilder

DEFAULT_RULES:List[absLinkBuilder] = [WikilinkBuilder(), MarkdownLinkBuilder()]

class LinkFactory:
    """Parses markdown content and builds :class:`Link` instances.

    The factory is bound to a concrete file and optional skill. It extracts
    both markdown-style links and wiki-style links, preserving their
    positions in the original content so callers can replace them later.
    """
    
    def __init__(self, rules:List[absLinkBuilder] = DEFAULT_RULES):
        self.__search_rules:List[absLinkBuilder] = rules
    
    def create_links(self, file: FileContext) -> List[Link]:
        """Parse all links from ``file`` and return them in source order."""
        content_context = ContentContext(file)
        links: List[Link] = []

        for rule in self.__search_rules:
            rule_links: List[Link] = rule.search(content_context)
            links.extend(rule_links)    

        links.sort(key=lambda link: link.context.start)
        return links

