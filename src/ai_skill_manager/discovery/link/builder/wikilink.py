"""Wiki link builder.

Builds :class:`absLink` objects from wiki-style references such as
``[[path]]`` and ``[[path|text]]``.

Сборщик wiki-ссылок.
Создаёт объекты :class:`absLink` из ссылок в стиле wiki, таких как
``[[path]]`` и ``[[path|text]]``.
"""

import re
from pathlib import Path
from typing import TYPE_CHECKING, List

from ....entities.link import PathLink, WebLink, absLink
from .abs_link_builder import absLinkBuilder

if TYPE_CHECKING:
    from ....entities.skill_file import SkillFile

# Regex for wiki links: optional "!", content inside double brackets.
# Регулярное выражение для wiki-ссылок: необязательный "!", содержимое внутри двойных скобок.
WIKI_LINK_RE = re.compile(r"!?\[\[([^\]]+)\]\]")


class WikilinkBuilder(absLinkBuilder):
    """Builds :class:`absLink` objects from wiki-style references.

    Builds :class:`absLink` objects from wiki-style references.

    Создаёт объекты :class:`absLink` из ссылок в стиле wiki.
    """

    def search(self, content: str, skill_file: "SkillFile") -> List[absLink]:
        """Parse all wiki-style links from ``content``.

        Parse all wiki-style links from ``content``.

        Разобрать все ссылки в стиле wiki из ``content``.

        Args:
            content: Markdown text to scan. / Markdown-текст для сканирования.
            skill_file: Skill file that contains the content.
                Файл скилла, содержащий содержимое.

        Returns:
            List of parsed link objects. / Список разобранных объектов ссылок.
        """
        links: List[absLink] = []
        # Iterate over every wiki link match in the content.
        # Перебираем каждое совпадение wiki-ссылки в содержимом.
        for match in WIKI_LINK_RE.finditer(content):
            links.append(self._build_wiki_link(match, skill_file))
        return links

    def _build_wiki_link(
        self,
        match: re.Match,
        skill_file: "SkillFile",
    ) -> absLink:
        """Convert a regex match into a link object.

        Convert a regex match into a link object.

        Преобразовать совпадение регулярного выражения в объект ссылки.

        Args:
            match: Regex match object for a wiki link. /
                Объект совпадения регулярного выражения для wiki-ссылки.
            skill_file: Skill file that contains the link. /
                Файл скилла, содержащий ссылку.

        Returns:
            A populated link instance. / Заполненный экземпляр ссылки.
        """
        raw = match.group(0)
        inner: str = match.group(1)

        # Wiki links support an optional display text after ``|``.
        # Wiki-ссылки поддерживают необязательный отображаемый текст после ``|``.
        if "|" in inner:
            left, custom_text = inner.rsplit("|", 1)
            if left.endswith("\\"):
                left = left[:-1]
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

        if self._is_http_link(path_clean):
            return WebLink(
                raw=raw,
                text=display_text,
                url=path_clean,
                format=WikilinkBuilder,
                start=start,
                end=end,
                skill_file_value=skill_file,
                header_value=fragment or None,
                is_image_value=self._is_image(raw),
            )

        return PathLink(
            raw=raw,
            text=display_text,
            format=WikilinkBuilder,
            start=start,
            end=end,
            skill_file_value=skill_file,
            raw_path=path_clean,
            header_value=fragment or None,
            is_image_value=self._is_image(raw),
        )
