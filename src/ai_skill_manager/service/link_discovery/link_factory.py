"""Factory for creating link objects from markdown content.

Factory for creating link objects from markdown content.

Фабрика для создания объектов ссылок из markdown-содержимого.
"""

from __future__ import annotations

from typing import List

from ...entities.link import LinkData
from .builder import absLinkBuilder, MarkdownLinkBuilder, WikilinkBuilder

# Registry of link builders used to scan content.
# Реестр сборщиков ссылок, используемых для сканирования содержимого.
LINK_SEARCH_RULES: List[absLinkBuilder] = [
    WikilinkBuilder(),
    MarkdownLinkBuilder(),
]


def search_links_in_content(content: str) -> List[LinkData]:
    """Parse all links from ``content`` and return them in source order.

    Parse all links from ``content`` and return them in source order.

    Разобрать все ссылки из ``content`` и вернуть их в порядке следования в тексте.

    Returns every syntactic match, including links inside ```example fenced
    code blocks - excluding those is a concern of
    ``exclude_rule.ExampleBlockExcludeRule``, applied later by
    ``LinkDiscovery``, not of this factory.

    Возвращает каждое синтаксическое совпадение, включая ссылки внутри
    fenced code block ```example - их исключение - забота
    ``exclude_rule.ExampleBlockExcludeRule``, применяемого позже
    ``LinkDiscovery``, а не этой фабрики.

    Args:
        content: Markdown text to scan. / Markdown-текст для сканирования.

    Returns:
        List of discovered link objects sorted by start position. /
        Список обнаруженных объектов ссылок, отсортированных по начальной позиции.
    """
    links: List[LinkData] = []

    # Run every registered builder against the content.
    # Запускаем каждый зарегистрированный сборщик на содержимом.
    for rule in LINK_SEARCH_RULES:
        rule_links: List[LinkData] = rule.search(content)
        links.extend(rule_links)

    # Sort by position so callers see links in document order.
    # Сортируем по позиции, чтобы вызывающий код видел ссылки в порядке документа.
    links.sort(key=lambda link: link.start)
    return links
