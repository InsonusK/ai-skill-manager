"""Abstract base class for classified links.

Абстрактный базовый класс для классифицированных ссылок.
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Type

from .link_data import LinkData


@dataclass(frozen=True)
class absLink(ABC):
    """Base type for a link once classified as a file reference or a web
    address. Never returned or constructed on its own - always one of its
    concrete subclasses (:class:`FileLink`, :class:`WebLink`), so a
    signature returning ``absLink`` unambiguously means "one of the
    classified kinds", never the raw parse result.

    Wraps the :class:`LinkData` produced by syntax parsing and forwards
    attribute access to it (``file_link.raw_path`` reads
    ``file_link.data.raw_path``), so callers do not need to know whether a
    field lives on the wrapper or the wrapped data.

    Базовый тип для ссылки после её классификации как файловой ссылки или
    веб-адреса. Никогда не возвращается и не создаётся сам по себе - всегда
    один из конкретных подклассов (:class:`FileLink`, :class:`WebLink`),
    поэтому сигнатура, возвращающая ``absLink``, однозначно означает "один из
    классифицированных видов", а не результат сырого разбора.

    Оборачивает :class:`LinkData`, полученный синтаксическим разбором, и
    перенаправляет доступ к атрибутам на него (``file_link.raw_path``
    читает ``file_link.data.raw_path``), поэтому вызывающему коду не нужно
    знать, находится ли поле на обёртке или на обёрнутых данных.

    Attributes:
        data: The raw, syntax-level link data this classified link was
            built from. / Сырые данные ссылки уровня синтаксиса, из которых
            построена эта классифицированная ссылка.
    """

    data: LinkData

    def __getattr__(self, name: str):
        """Forward attribute access to the wrapped :class:`LinkData`.

        Перенаправляет доступ к атрибутам на обёрнутый :class:`LinkData`.
        """
        return getattr(self.data, name)

    @property
    def link_type(self) -> Type["absLink"]:
        """Return the concrete link class.

        Вернуть конкретный класс ссылки.

        Returns:
            The class of the link instance. / Класс экземпляра ссылки.
        """
        return type(self)
