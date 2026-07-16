"""Abstract skill source.

Абстрактный источник навыков.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass(frozen=True)
class ScanLocation:
    """Filesystem location produced by a source for discovery.

    Локация файловой системы, которую источник предоставляет для обнаружения.

    Attributes:
        repo_path: Absolute path to the repository root. Used for
            ``repo_absolute`` link resolution.
            Абсолютный путь к корню репозитория. Используется для
            разрешения ссылок ``repo_absolute``.
        scan_path: Absolute path to the directory that should be scanned
            for skills. This becomes ``Skill.scan_path``.
            Абсолютный путь к директории, которую следует сканировать
            на наличие навыков. Становится ``Skill.scan_path``.
    """

    repo_path: Path
    scan_path: Path


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
    def __str__(self) -> str:
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

    @abstractmethod
    def get_scan_locations(self) -> List[ScanLocation]:
        """Return the filesystem locations this source refers to.

        Вернуть файловые локации, на которые ссылается этот источник.

        A source may hold several scan paths (e.g. several GitHub subpaths).
        For remote sources such as GitHub this method may download and
        extract the repository once before returning all resulting paths.

        Источник может содержать несколько путей сканирования (например,
        несколько подпутей GitHub). Для удалённых источников, таких как
        GitHub, этот метод может один раз скачать и распаковать репозиторий
        перед возвратом всех получившихся путей.

        Returns:
            A list of :class:`ScanLocation`, each with ``repo_path`` and
            ``scan_path``. / Список :class:`ScanLocation`, каждый с полями
            ``repo_path`` и ``scan_path``.
        """
        ...

    def cleanup(self) -> None:
        """Release any temporary resources acquired by this source.

        Освободить временные ресурсы, полученные этим источником.

        The default implementation does nothing. Sources that create temporary
        directories (e.g. GitHub) should override this method.

        Реализация по умолчанию ничего не делает. Источники, создающие
        временные директории (например, GitHub), должны переопределить
        этот метод.
        """
