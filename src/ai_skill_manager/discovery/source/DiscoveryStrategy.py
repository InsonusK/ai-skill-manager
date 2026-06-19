from logging import Logger
from ...models import Skill
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

logger = Logger("DiscoveryStrategy")
class DiscoveryStrategy(ABC):
    """Abstract base for skill discovery strategies."""

    def __init__(self, source_path: Path):
        if not source_path.exists():
            logger.error("source_path not found: %s", source_path)
        self.source_path = source_path.resolve()

    @abstractmethod
    def discover(self) -> List[Skill]:
        """Discover skills and return list of Skill objects."""
        pass
