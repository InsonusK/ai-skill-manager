"""Markdown link builder.

Builds :class:`Link` objects from Markdown-style references such as
``[text](path)`` and ``![alt](path)``.

Сборщик ссылок Markdown.
Создаёт объекты :class:`Link` из ссылок в стиле Markdown, таких как
``[text](path)`` и ``![alt](path)``.
"""

import re
from typing import List

from ....entities.link import Link
from .abs_link_builder import absLinkBuilder

# Regex for Markdown links: optional "!", text in brackets, path in parentheses.
# Регулярное выражение для ссылок Markdown: необязательный "!", текст в скобках,
# путь в круглых скобках.
MD_LINK_RE = re.compile(r'!?\[([^\]]*)\]\(([^\s\)"]*)\)')


class MarkdownLinkBuilder(absLinkBuilder):
    """Builds :class:`Link` objects from Markdown-style references.

    Builds :class:`Link` objects from Markdown-style references.

    Создаёт объекты :class:`Link` из ссылок в стиле Markdown.
    """

    def search(self, content: str) -> List[Link]:
        """Parse all Markdown-style links from ``content``.

        Parse all Markdown-style links from ``content``.

        Разобрать все ссылки в стиле Markdown из ``content``.

        Args:
            content: Markdown text to scan. / Markdown-текст для сканирования.

        Returns:
            List of parsed :class:`Link` objects. /
            Список разобранных объектов :class:`Link`.
        """
        links: List[Link] = []
        # Iterate over every Markdown link match in the content.
        # Перебираем каждое совпадение Markdown-ссылки в содержимом.
        for match in MD_LINK_RE.finditer(content):
            links.append(self._build_markdown_link(match))
        return links

    def _build_markdown_link(self, match: re.Match) -> Link:
        """Convert a regex match into a :class:`Link`.

        Convert a regex match into a :class:`Link`.

        Преобразовать совпадение регулярного выражения в :class:`Link`.

        Args:
            match: Regex match object for a Markdown link. /
                Объект совпадения регулярного выражения для Markdown-ссылки.

        Returns:
            A populated :class:`Link` instance. /
            Заполненный экземпляр :class:`Link`.
        """
        raw: str = match.group(0)
        text = match.group(1)
        path_raw = match.group(2)
        # Separate the URL fragment (#header) from the path.
        # Отделяем фрагмент URL (#заголовок) от пути.
        path_clean, header = self._split_fragment(path_raw)
        start = match.start()
        end = match.end()

        return Link(
            raw=raw,
            path=path_clean,
            text=text,
            kind=self._get_kind(path_clean),
            format="markdown",
            start=start,
            end=end,
            header=header or None,
            is_image=self._is_image(raw),
        )
