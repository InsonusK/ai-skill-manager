"""Factory for creating :class:`Link` objects from markdown content.

Factory for creating :class:`Link` objects from markdown content.

Фабрика для создания объектов :class:`Link` из markdown-содержимого.
"""

from typing import List

from ....entities.link import Link
from .builder import absLinkBuilder, MarkdownLinkBuilder, WikilinkBuilder

# Registry of link builders used to scan content.
# Реестр сборщиков ссылок, используемых для сканирования содержимого.
LINK_SEARCH_RULES: List[absLinkBuilder] = [
    WikilinkBuilder(),
    MarkdownLinkBuilder(),
]


def search_links_in_content(content: str) -> List[Link]:
    """Parse all links from ``content`` and return them in source order.

    Parse all links from ``content`` and return them in source order.

    Разобрать все ссылки из ``content`` и вернуть их в порядке следования в тексте.

    Args:
        content: Markdown text to scan. / Markdown-текст для сканирования.

    Returns:
        List of discovered :class:`Link` objects sorted by start position. /
        Список обнаруженных объектов :class:`Link`, отсортированных по начальной позиции.
    """
    links: List[Link] = []

    # Run every registered builder against the content.
    # Запускаем каждый зарегистрированный сборщик на содержимом.
    for rule in LINK_SEARCH_RULES:
        rule_links: List[Link] = rule.search(content)
        links.extend(rule_links)

    # Sort by position so callers see links in document order.
    # Сортируем по позиции, чтобы вызывающий код видел ссылки в порядке документа.
    links.sort(key=lambda link: link.start)
    return links
