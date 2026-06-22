"""Link factory package.

Exports the public entry point for searching links inside markdown content.

Пакет фабрики ссылок.
Экспортирует публичную точку входа для поиска ссылок внутри markdown-содержимого.
"""

from .link_factory import search_links_in_content

__all__ = [
    "search_links_in_content",
]
