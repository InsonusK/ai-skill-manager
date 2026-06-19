"""Abstract base class for skill discovery strategies.

Абстрактный базовый класс для стратегий обнаружения навыков.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from ...models import Skill

# Module logger / Логгер модуля.
logger = logging.getLogger(__name__)


class DiscoveryStrategy(ABC):
    """Abstract base for skill discovery strategies.

    Concrete strategies receive a source path (file or directory) and must
    return a list of discovered :class:`Skill` objects.

    Абстрактный базовый класс для стратегий обнаружения навыков.
    Конкретные стратегии получают путь к источнику (файл или директорию)
    и должны вернуть список обнаруженных объектов :class:`Skill`.
    """

    def __init__(self, source_path: Path):
        """Initialize the strategy with a source path.

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
    def discover(self) -> List[Skill]:
        """Discover skills and return a list of Skill objects.

        Обнаружить навыки и вернуть список объектов Skill.

        Returns:
            List of discovered skills. / Список обнаруженных навыков.
        """
        pass
