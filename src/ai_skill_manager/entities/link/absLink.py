"""Abstract base class for all links found in markdown content.

Абстрактный базовый класс для всех ссылок, найденных в markdown-содержимом.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Literal, Optional, Type


@dataclass(frozen=True)
class absLink(ABC):
    """Abstract base class for all links found in markdown content.

    Holds the fields that are common to every kind of link: the raw source
    text, display text, format, offsets and optional fragment.

    Базовый абстрактный класс для всех ссылок, найденных в markdown-содержимом.
    Содержит общие для любого вида ссылки поля: исходный текст, отображаемый
    текст, формат, смещения и опциональный фрагмент.

    Attributes:
        raw: The exact link text as it appears in the source.
            Точный текст ссылки в исходнике.
        text: The display text of the link.
            Отображаемый текст ссылки.
        format: Whether the link was written as markdown or wiki link.
            Была ли ссылка записана как markdown- или wiki-ссылка.
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
    format: Literal["markdown", "wiki"]
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

    @property
    @abstractmethod
    def target(self) -> str:
        """Return the link target as a string.

        Вернуть цель ссылки в виде строки.

        Returns:
            For path links the formatted path, for web links the URL.
            Для путевых ссылок — форматированный путь, для веб-ссылок — URL.
        """
        ...
