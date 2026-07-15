"""Abstract base class for link builders.

Provides the shared image-flag helper used by concrete builders. Raw path
classification (web vs. file, relative vs. absolute) is not this class's
concern - it lives in ``tools.link_path`` and is applied later, after
parsing, not while scanning syntax.

Абстрактный базовый класс для сборщиков ссылок.
Предоставляет общий вспомогательный метод для флага изображения,
используемый конкретными сборщиками. Классификация сырого пути (web или
файл, относительный или абсолютный) - не забота этого класса - она находится
в ``tools.link_path`` и применяется позже, после разбора, а не во время
сканирования синтаксиса.
"""

from abc import ABC
from typing import List
from ....entities.link import LinkData

class absLinkBuilder(ABC):
    """Base class for all link builders.

    Subclasses must implement :meth:`search`. Only pure syntax concerns
    (e.g. detecting an image marker) are shared here.

    Базовый класс для всех сборщиков ссылок.
    Подклассы должны реализовать :meth:`search`. Здесь общими являются
    только чисто синтаксические аспекты (например, обнаружение маркера
    изображения).
    """

    def search(self, content: str) -> List[LinkData]:
        """Search ``content`` for links supported by this builder.

        Search ``content`` for links supported by this builder.

        Искать в ``content`` ссылки, поддерживаемые этим сборщиком.

        Args:
            content: Markdown text to scan. / Markdown-текст для сканирования.

        Returns:
            List of matched link objects. / Список найденных объектов ссылок.
        """
        ...

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
