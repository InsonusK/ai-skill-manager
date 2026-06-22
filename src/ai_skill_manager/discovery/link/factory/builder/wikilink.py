"""Wiki link builder.

Builds :class:`Link` objects from wiki-style references such as
``[[path]]`` and ``[[path|text]]``.

Сборщик wiki-ссылок.
Создаёт объекты :class:`Link` из ссылок в стиле wiki, таких как
``[[path]]`` и ``[[path|text]]``.
"""

import re
from pathlib import Path
from typing import List

from .....entities.link import Link
from .abs_link_builder import absLinkBuilder

# Regex for wiki links: optional "!", content inside double brackets.
# Регулярное выражение для wiki-ссылок: необязательный "!", содержимое внутри двойных скобок.
WIKI_LINK_RE = re.compile(r"!?\[\[([^\]]+)\]\]")


class WikilinkBuilder(absLinkBuilder):
    """Builds :class:`Link` objects from wiki-style references.

    Builds :class:`Link` objects from wiki-style references.

    Создаёт объекты :class:`Link` из ссылок в стиле wiki.
    """

    def search(self, content: str) -> List[Link]:
        """Parse all wiki-style links from ``content``.

        Parse all wiki-style links from ``content``.

        Разобрать все ссылки в стиле wiki из ``content``.

        Args:
            content: Markdown text to scan. / Markdown-текст для сканирования.

        Returns:
            List of parsed :class:`Link` objects. /
            Список разобранных объектов :class:`Link`.
        """
        links: List[Link] = []
        # Iterate over every wiki link match in the content.
        # Перебираем каждое совпадение wiki-ссылки в содержимом.
        for match in WIKI_LINK_RE.finditer(content):
            links.append(self._build_wiki_link(match))
        return links

    def _build_wiki_link(self, match: re.Match) -> Link:
        """Convert a regex match into a :class:`Link`.

        Convert a regex match into a :class:`Link`.

        Преобразовать совпадение регулярного выражения в :class:`Link`.

        Args:
            match: Regex match object for a wiki link. /
                Объект совпадения регулярного выражения для wiki-ссылки.

        Returns:
            A populated :class:`Link` instance. /
            Заполненный экземпляр :class:`Link`.
        """
        raw = match.group(0)
        inner = match.group(1)

        # Wiki links support an optional display text after ``|``.
        # Wiki-ссылки поддерживают необязательный отображаемый текст после ``|``.
        if "|" in inner:
            left, custom_text = inner.rsplit("|", 1)
        else:
            left = inner
            custom_text = None

        path_clean, fragment = self._split_fragment(left)
        # Use the basename as display text when no custom text is provided.
        # Используем базовое имя файла в качестве отображаемого текста,
        # если не задан пользовательский текст.
        display_text = custom_text if custom_text is not None else Path(path_clean).name
        start = match.start()
        end = match.end()

        return Link(
            raw=raw,
            path=path_clean,
            text=display_text,
            kind=self._get_kind(path_clean),
            format="wiki",
            start=start,
            end=end,
            header=fragment or None,
            is_image=self._is_image(raw),
        )
