"""Abstract base class for all links found in markdown content.

Абстрактный базовый класс для всех ссылок, найденных в markdown-содержимом.
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional, Type

if TYPE_CHECKING:
    from ...discovery.link.builder.abs_link_builder import absLinkBuilder


@dataclass(frozen=True)
class absLink(ABC):
    """Abstract base class for all links found in markdown content.

    Holds the fields that are common to every kind of link: the raw source
    text, display text, builder format, offsets, optional fragment and image
    flag. Target *resolution* is not this class's concern - it is done later,
    against the raw path, by ``entities.link.file_link_factory.FileLinkFactory``.

    Базовый абстрактный класс для всех ссылок, найденных в markdown-содержимом.
    Содержит общие для любого вида ссылки поля: исходный текст, отображаемый
    текст, формат сборщика, смещения, опциональный фрагмент и флаг
    изображения. *Резолюция* цели - не забота этого класса, она выполняется
    позже, над сырым путём, в ``entities.link.file_link_factory.FileLinkFactory``.

    Attributes:
        raw: The exact link text as it appears in the source.
            Точный текст ссылки в исходнике.
        text: The display text of the link.
            Отображаемый текст ссылки.
        format: Builder class that created this link (markdown or wiki).
            Класс сборщика, создавшего эту ссылку (markdown или wiki).
        start: Character offset where the link starts in the source content.
            Смещение символа, с которого ссылка начинается в исходном тексте.
        end: Character offset where the link ends in the source content.
            Смещение символа, на котором ссылка заканчивается в исходном тексте.
        header: The optional ``#fragment`` part of the link target.
            Опциональная часть фрагмента ``#fragment`` цели ссылки.
        is_image: ``True`` for image links (``![...](...)``).
            ``True`` для ссылок-изображений (``![...](...)``).
    """

    raw: str
    text: str
    format: Type["absLinkBuilder"]
    start: int
    end: int
    header: Optional[str] = field(init=False)
    is_image: bool = field(init=False)

    @property
    def link_type(self) -> Type["absLink"]:
        """Return the concrete link class.

        Вернуть конкретный класс ссылки.

        Returns:
            The class of the link instance. / Класс экземпляра ссылки.
        """
        return type(self)
