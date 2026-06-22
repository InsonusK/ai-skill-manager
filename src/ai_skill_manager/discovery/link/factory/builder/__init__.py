"""Link builder implementations.

Provides concrete builders for Markdown and wiki-style links.

Реализации сборщиков ссылок.
Предоставляет конкретные сборщики для ссылок в стиле Markdown и wiki.
"""

from .abs_link_builder import absLinkBuilder
from .markdown import MarkdownLinkBuilder
from .wikilink import WikilinkBuilder

__all__ = [
    "absLinkBuilder",
    "MarkdownLinkBuilder",
    "WikilinkBuilder",
]
