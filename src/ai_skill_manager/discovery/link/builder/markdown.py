"""Markdown link builder.

Builds :class:`absLink` objects from Markdown-style references such as
``[text](path)`` and ``![alt](path)``.

Сборщик ссылок Markdown.
Создаёт объекты :class:`absLink` из ссылок в стиле Markdown, таких как
``[text](path)`` и ``![alt](path)``.
"""

import re
from typing import TYPE_CHECKING, List

from ....entities.link import PathLink, WebLink, absLink
from .abs_link_builder import absLinkBuilder

if TYPE_CHECKING:
    from ....entities.skill_file import SkillFile

# Regex for Markdown links: optional "!", text in brackets, path in parentheses.
# Регулярное выражение для ссылок Markdown: необязательный "!", текст в скобках,
# путь в круглых скобках.
MD_LINK_RE = re.compile(r'!?\[([^\]]*)\]\(([^\s\)"]*)\)')


class MarkdownLinkBuilder(absLinkBuilder):
    """Builds :class:`absLink` objects from Markdown-style references.

    Builds :class:`absLink` objects from Markdown-style references.

    Создаёт объекты :class:`absLink` из ссылок в стиле Markdown.
    """

    def search(self, content: str, skill_file: "SkillFile") -> List[absLink]:
        """Parse all Markdown-style links from ``content``.

        Parse all Markdown-style links from ``content``.

        Разобрать все ссылки в стиле Markdown из ``content``.

        Args:
            content: Markdown text to scan. / Markdown-текст для сканирования.
            skill_file: Skill file that contains the content.
                Файл скилла, содержащий содержимое.

        Returns:
            List of parsed link objects. / Список разобранных объектов ссылок.
        """
        links: List[absLink] = []
        # Iterate over every Markdown link match in the content.
        # Перебираем каждое совпадение Markdown-ссылки в содержимом.
        for match in MD_LINK_RE.finditer(content):
            links.append(self._build_markdown_link(match, skill_file))
        return links

    def _build_markdown_link(
        self,
        match: re.Match,
        skill_file: "SkillFile",
    ) -> absLink:
        """Convert a regex match into a link object.

        Convert a regex match into a link object.

        Преобразовать совпадение регулярного выражения в объект ссылки.

        Args:
            match: Regex match object for a Markdown link. /
                Объект совпадения регулярного выражения для Markdown-ссылки.
            skill_file: Skill file that contains the link. /
                Файл скилла, содержащий ссылку.

        Returns:
            A populated link instance. / Заполненный экземпляр ссылки.
        """
        raw: str = match.group(0)
        text = match.group(1)
        path_raw = match.group(2)
        # Separate the URL fragment (#header) from the path.
        # Отделяем фрагмент URL (#заголовок) от пути.
        path_clean, header = self._split_fragment(path_raw)
        start = match.start()
        end = match.end()

        if self._is_http_link(path_clean):
            return WebLink(
                raw=raw,
                text=text,
                path=path_clean,
                format="markdown",
                start=start,
                end=end,
                header_value=header or None,
                is_image_value=self._is_image(raw),
            )

        return PathLink(
            raw=raw,
            text=text,
            format="markdown",
            start=start,
            end=end,
            skill_file=skill_file,
            raw_path=path_clean,
            header_value=header or None,
            is_image_value=self._is_image(raw),
        )
