"""Factory for creating link objects from markdown content.

Factory for creating link objects from markdown content.

Фабрика для создания объектов ссылок из markdown-содержимого.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from ...entities.link import absLink
from .builder import absLinkBuilder, MarkdownLinkBuilder, WikilinkBuilder

if TYPE_CHECKING:
    from ...entities.skill_file import SkillFile

# Registry of link builders used to scan content.
# Реестр сборщиков ссылок, используемых для сканирования содержимого.
LINK_SEARCH_RULES: List[absLinkBuilder] = [
    WikilinkBuilder(),
    MarkdownLinkBuilder(),
]


def search_links_in_content(
    content: str, skill_file: "SkillFile"
) -> List[absLink]:
    """Parse all links from ``content`` and return them in source order.

    Parse all links from ``content`` and return them in source order.

    Разобрать все ссылки из ``content`` и вернуть их в порядке следования в тексте.

    Args:
        content: Markdown text to scan. / Markdown-текст для сканирования.
        skill_file: Skill file that contains the content.
            Файл скилла, содержащий содержимое.

    Returns:
        List of discovered link objects sorted by start position. /
        Список обнаруженных объектов ссылок, отсортированных по начальной позиции.
    """
    links: List[absLink] = []

    # Run every registered builder against the content.
    # Запускаем каждый зарегистрированный сборщик на содержимом.
    for rule in LINK_SEARCH_RULES:
        rule_links: List[absLink] = rule.search(content, skill_file)
        links.extend(rule_links)

    # Sort by position so callers see links in document order.
    # Сортируем по позиции, чтобы вызывающий код видел ссылки в порядке документа.
    links.sort(key=lambda link: link.start)
    return links
