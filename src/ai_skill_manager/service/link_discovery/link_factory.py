"""Factory for creating link objects from markdown content.

Factory for creating link objects from markdown content.

Фабрика для создания объектов ссылок из markdown-содержимого.
"""

from __future__ import annotations

import re
from typing import List

from ...entities.link import absLink
from .builder import absLinkBuilder, MarkdownLinkBuilder, WikilinkBuilder

# Registry of link builders used to scan content.
# Реестр сборщиков ссылок, используемых для сканирования содержимого.
LINK_SEARCH_RULES: List[absLinkBuilder] = [
    WikilinkBuilder(),
    MarkdownLinkBuilder(),
]

# Matches fenced code blocks labelled ``example`` (optionally indented by up to
# three spaces, per CommonMark). The content is replaced with spaces before
# searching for links so that offsets in the original text remain valid while
# links inside the block are ignored.
# Совпадает с fenced code blocks, помеченными ``example`` (с отступом до трёх
# пробелов, как в CommonMark). Содержимое заменяется пробелами перед поиском
# ссылок, чтобы смещения в оригинальном тексте оставались корректными, а
# ссылки внутри блока игнорировались.
_EXAMPLE_BLOCK_RE = re.compile(
    r"^[ ]{0,3}```example\s*$\n?.*?^[ ]{0,3}(?:```\s*$|\Z)",
    re.MULTILINE | re.DOTALL,
)


def _mask_example_blocks(content: str) -> str:
    """Replace every `` ```example `` code block with spaces.

    The returned string has exactly the same length as ``content`` so that link
    offsets computed from it stay valid for the original document.

    Возвращает строку той же длины, что и ``content``, чтобы смещения ссылок,
    вычисленные из неё, оставались корректными для оригинального документа.
    """

    def _replace_with_spaces(match: re.Match) -> str:
        return " " * len(match.group(0))

    return _EXAMPLE_BLOCK_RE.sub(_replace_with_spaces, content)


def search_links_in_content(content: str) -> List[absLink]:
    """Parse all links from ``content`` and return them in source order.

    Parse all links from ``content`` and return them in source order.

    Разобрать все ссылки из ``content`` и вернуть их в порядке следования в тексте.

    Args:
        content: Markdown text to scan. / Markdown-текст для сканирования.

    Returns:
        List of discovered link objects sorted by start position. /
        Список обнаруженных объектов ссылок, отсортированных по начальной позиции.
    """
    links: List[absLink] = []

    # Hide links inside ```example blocks while keeping all character offsets
    # unchanged so that later replacements use correct positions.
    # Скрываем ссылки внутри блоков ```example, сохраняя смещения символов,
    # чтобы последующие замены использовали корректные позиции.
    masked_content = _mask_example_blocks(content)

    # Run every registered builder against the content.
    # Запускаем каждый зарегистрированный сборщик на содержимом.
    for rule in LINK_SEARCH_RULES:
        rule_links: List[absLink] = rule.search(masked_content)
        links.extend(rule_links)

    # Sort by position so callers see links in document order.
    # Сортируем по позиции, чтобы вызывающий код видел ссылки в порядке документа.
    links.sort(key=lambda link: link.start)
    return links
