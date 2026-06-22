"""Abstract skill source.

Абстрактный источник навыков.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict

@dataclass(frozen=True)
class Source(ABC):
    """Abstract representation of a skill source.

    A source encapsulates the origin of one or more skills: a local directory
    or file, a GitHub repository, or any other future location.

    Абстрактное представление источника навыков.
    Источник инкапсулирует происхождение одного или нескольких навыков:
    локальную директорию или файл, репозиторий GitHub или любое другое
    будущее расположение.
    """
    @abstractmethod
    def __str__(self)->str:
        ...
    @property
    @abstractmethod
    def source_type(self) -> str:
        """Return the source type identifier.

        Вернуть идентификатор типа источника.

        Returns:
            Short source type name, e.g. ``github`` or ``local``.
            Короткое имя типа источника, например ``github`` или ``local``.
        """
        ...

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Return a serializable dictionary representation.

        Вернуть сериализуемое словарное представление.

        Returns:
            Dictionary with source metadata. / Словарь с метаданными источника.
        """
        ...
