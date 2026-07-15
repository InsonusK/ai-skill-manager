"""Markdown link builder.

Builds :class:`LinkData` records from Markdown-style references such as
``[text](path)`` and ``![alt](path)``.

Сборщик ссылок Markdown.
Создаёт записи :class:`LinkData` из ссылок в стиле Markdown, таких как
``[text](path)`` и ``![alt](path)``.
"""

import re
from typing import List

from ....tools.link_path import split_fragment
from .abs_link_builder import absLinkBuilder, LinkData

# Regex for Markdown links: optional "!", text in brackets, path in parentheses.
# Регулярное выражение для ссылок Markdown: необязательный "!", текст в скобках,
# путь в круглых скобках.
MD_LINK_RE = re.compile(r'!?\[([^\]]*)\]\(([^\s\)"]*)\)')


class MarkdownLinkBuilder(absLinkBuilder):
    """Builds :class:`LinkData` records from Markdown-style references.

    Builds :class:`LinkData` records from Markdown-style references.

    Создаёт записи :class:`LinkData` из ссылок в стиле Markdown.
    """

    def search(self, content: str) -> List[LinkData]:
        """Parse all Markdown-style links from ``content``.

        Parse all Markdown-style links from ``content``.

        Разобрать все ссылки в стиле Markdown из ``content``.

        Args:
            content: Markdown text to scan. / Markdown-текст для сканирования.

        Returns:
            List of parsed link records. / Список разобранных записей ссылок.
        """
        links: List[LinkData] = []
        # Iterate over every Markdown link match in the content.
        # Перебираем каждое совпадение Markdown-ссылки в содержимом.
        for match in MD_LINK_RE.finditer(content):
            links.append(self._build_markdown_link(match))
        return links

    def _build_markdown_link(self, match: re.Match) -> LinkData:
        """Convert a regex match into a raw link record.

        Convert a regex match into a raw link record.

        Преобразовать совпадение регулярного выражения в сырую запись ссылки.

        Args:
            match: Regex match object for a Markdown link. /
                Объект совпадения регулярного выражения для Markdown-ссылки.

        Returns:
            A populated, not-yet-classified link record. /
            Заполненная, ещё не классифицированная запись ссылки.
        """
        raw: str = match.group(0)
        text = match.group(1)
        path_raw = match.group(2)
        # Separate the URL fragment (#header) from the path.
        # Отделяем фрагмент URL (#заголовок) от пути.
        path_clean, header = split_fragment(path_raw)
        start = match.start()
        end = match.end()

        return LinkData(
            raw=raw,
            text=text,
            format="markdown",
            start=start,
            end=end,
            raw_path=path_clean,
            header=header or None,
            is_image=self._is_image(raw),
        )
