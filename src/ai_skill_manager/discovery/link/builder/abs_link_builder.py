"""Abstract base class for link builders.

Provides shared helpers for classifying link paths and splitting fragments.

Абстрактный базовый класс для сборщиков ссылок.
Предоставляет общие вспомогательные методы для классификации путей ссылок
и разделения фрагментов.
"""

from abc import ABC
from typing import TYPE_CHECKING, List, Tuple

from ....entities.link_kind import LinkKind

if TYPE_CHECKING:
    from ....entities.skill_file import SkillFile


class absLinkBuilder(ABC):
    """Base class for all link builders.

    Subclasses must implement :meth:`search` and may reuse the helpers defined
    here to classify paths and split fragments.

    Базовый класс для всех сборщиков ссылок.
    Подклассы должны реализовать :meth:`search` и могут использовать
    определённые здесь вспомогательные методы для классификации путей
    и разделения фрагментов.
    """

    def search(self, content: str, skill_file: "SkillFile") -> List:
        """Search ``content`` for links supported by this builder.

        Search ``content`` for links supported by this builder.

        Искать в ``content`` ссылки, поддерживаемые этим сборщиком.

        Args:
            content: Markdown text to scan. / Markdown-текст для сканирования.
            skill_file: Skill file that contains the content.
                Файл скилла, содержащий содержимое.

        Returns:
            List of matched link objects. / Список найденных объектов ссылок.
        """
        ...

    def _split_fragment(self, path: str) -> Tuple[str, str]:
        """Split a path into path and ``#fragment`` parts.

        Split a path into path and ``#fragment`` parts.

        Разделить путь на часть пути и часть ``#fragment``.

        Args:
            path: Raw link path possibly containing ``#``. /
                Исходный путь ссылки, возможно содержащий ``#``.

        Returns:
            Tuple of (path_without_fragment, fragment_or_empty_string). /
            Кортеж (путь_без_фрагмента, фрагмент_или_пустая_строка).
        """
        if "#" in path:
            path_clean, header = path.split("#", 1)
            return path_clean, f"#{header}"
        return path, ""

    def _is_image(self, raw: str) -> bool:
        """Return ``True`` if the raw link is an image reference.

        Return ``True`` if the raw link is an image reference.

        Вернуть ``True``, если исходная ссылка является ссылкой на изображение.

        Args:
            raw: Raw link text including markers. /
                Исходный текст ссылки, включая маркеры.

        Returns:
            ``True`` when the link starts with ``!``. /
            ``True``, когда ссылка начинается с ``!``.
        """
        return raw.startswith("!")

    def _get_kind(self, path: str) -> LinkKind:
        """Classify a local link path into a :class:`LinkKind`.

        Classify a local link path into a :class:`LinkKind`.

        Классифицировать локальный путь ссылки по значению :class:`LinkKind`.

        Args:
            path: Clean link path without fragment. /
                Очищенный путь ссылки без фрагмента.

        Returns:
            The determined link kind. / Определённый вид ссылки.

        Raises:
            ValueError: If the path cannot be classified or is a web URI. /
                Если путь невозможно классифицировать или является веб-URI.
        """
        if self._is_relative(path):
            return LinkKind.relative
        elif self._is_os_absolute(path):
            return LinkKind.os_absolute
        elif self._is_http_link(path):
            raise ValueError(f"Web links are represented by WebLink: {path}")
        else:
            return LinkKind.repo_absolute

    def _is_http_link(self, path: str) -> bool:
        """Return ``True`` for web/mailto/ftp/file links.

        Return ``True`` for web/mailto/ftp/file links.

        Вернуть ``True`` для web/mailto/ftp/file ссылок.

        Args:
            path: Link path to check. / Путь ссылки для проверки.

        Returns:
            ``True`` for links starting with common URI schemes. /
            ``True`` для ссылок, начинающихся с распространённых URI-схем.
        """
        lower = path.lower()
        return lower.startswith(("http://", "https://", "mailto:", "ftp://", "file://"))

    def _is_relative(self, path: str) -> bool:
        """Return ``True`` for links starting with ``./`` or ``../``.

        Return ``True`` for links starting with ``./`` or ``../``.

        Вернуть ``True`` для ссылок, начинающихся с ``./`` или ``../``.

        Args:
            path: Link path to check. / Путь ссылки для проверки.

        Returns:
            ``True`` when the path is a relative filesystem reference. /
            ``True``, когда путь является относительной файловой ссылкой.
        """
        return path.startswith(("./", "../"))

    def _is_os_absolute(self, path: str) -> bool:
        """Return ``True`` for OS-absolute paths starting with ``/``.

        Return ``True`` for OS-absolute paths starting with ``/``.

        Вернуть ``True`` для абсолютных путей ОС, начинающихся с ``/``.

        Args:
            path: Link path to check. / Путь ссылки для проверки.

        Returns:
            ``True`` when the path is absolute on the local filesystem. /
            ``True``, когда путь абсолютен в локальной файловой системе.
        """
        return path.startswith("/")
