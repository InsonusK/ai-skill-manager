"""Abstract base class for skill discovery strategies.

Defines the interface that all discovery strategies must implement.

Абстрактный базовый класс для стратегий обнаружения навыков.
Определяет интерфейс, который должны реализовывать все стратегии обнаружения.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple

from ....entities.skill_v2 import Skill

# Module logger / Логгер модуля.
logger = logging.getLogger(__name__)


class absDiscoveryStrategy(ABC):
    """Abstract base for skill discovery strategies.

    Concrete strategies receive a source path (file or directory) and must
    return the discovered :class:`Skill` objects plus any per-candidate
    errors (e.g. a missing frontmatter name) collected along the way.
    Structural conflicts (e.g. ambiguous pattern matches) are not collected -
    they still raise, since there is no single reasonable skill to fall back
    to for that path.

    Абстрактный базовый класс для стратегий обнаружения навыков.
    Конкретные стратегии получают путь к источнику (файл или директорию) и
    должны вернуть обнаруженные объекты :class:`Skill` плюс любые ошибки по
    отдельным кандидатам (например, отсутствующее имя во frontmatter),
    собранные по пути. Структурные конфликты (например, неоднозначные
    совпадения паттернов) не собираются - они по-прежнему вызывают
    исключение, так как для такого пути нет одного разумного скилла, на
    который можно было бы откатиться.
    """

    def __init__(self, source_path: Path):
        """Initialize the strategy with a source path.

        Initialize the strategy with a source path.

        Инициализировать стратегию путём к источнику.

        Args:
            source_path: Path to scan. / Путь для сканирования.
        """
        if not source_path.exists():
            # Log missing source but keep the path for downstream handling.
            # Логируем отсутствующий источник, но сохраняем путь для дальнейшей обработки.
            logger.error("source_path not found: %s", source_path)
        # Store the absolute path to avoid ambiguity during scanning.
        # Сохраняем абсолютный путь, чтобы избежать неоднозначности при сканировании.
        self.source_path = source_path.resolve()

    @abstractmethod
    def discover(self) -> Tuple[List[Skill], List[str]]:
        """Discover skills and return them plus any collected errors.

        Discover skills and return them plus any collected errors.

        Обнаружить навыки и вернуть их вместе с собранными ошибками.

        Returns:
            The discovered skills and per-candidate error messages. /
            Обнаруженные скиллы и сообщения об ошибках по кандидатам.
        """
        pass
