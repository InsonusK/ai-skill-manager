"""Abstract base class for all links found in markdown content.

Абстрактный базовый класс для всех ссылок, найденных в markdown-содержимом.
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional, Type

from .link_kind import LinkKind

if TYPE_CHECKING:
    from ...discovery.link.builder.abs_link_builder import absLinkBuilder
    from ..skill_file import SkillFile
    from .link_path import LinkPath


@dataclass(frozen=True)
class absLink(ABC):
    """Abstract base class for all links found in markdown content.

    Holds the fields that are common to every kind of link: the raw source
    text, resolved target information, display text, builder format, offsets,
    optional fragment, image flag and owning skill file.

    Базовый абстрактный класс для всех ссылок, найденных в markdown-содержимом.
    Содержит общие для любого вида ссылки поля: исходный текст, разрешённую
    информацию о цели, отображаемый текст, формат сборщика, смещения,
    опциональный фрагмент, флаг изображения и файл скилла, которому принадлежит
    ссылка.

    Attributes:
        raw: The exact link text as it appears in the source.
            Точный текст ссылки в исходнике.
        kind: Where the resolved link points (skill, source or external).
            Куда ведёт разрешённая ссылка (skill, source или external).
        path: Resolved path information for the link target.
            Разрешённая информация о пути цели ссылки.
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
        skill_file: The skill file that contains the link.
            Файл скилла, содержащий ссылку.
    """

    raw: str
    path: "LinkPath" = field(init=False)
    text: str
    format: Type["absLinkBuilder"]
    start: int
    end: int
    header: Optional[str] = field(init=False)
    is_image: bool = field(init=False)
    skill_file: Optional["SkillFile"] = field(init=False)

    @property
    def link_type(self) -> Type["absLink"]:
        """Return the concrete link class.

        Вернуть конкретный класс ссылки.

        Returns:
            The class of the link instance. / Класс экземпляра ссылки.
        """
        return type(self)

    @property
    def target(self) -> str:
        """Return the normalized link target.

        Вернуть нормализованную цель ссылки.

        Returns:
            The formatted target path or URL.
            Отформатированный путь цели или URL.
        """
        return self.path.formatted
