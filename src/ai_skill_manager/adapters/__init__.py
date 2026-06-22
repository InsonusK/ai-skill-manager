"""Public API for skill file adaptation.

Exports the main ``Adapter`` orchestrator, the default adaptation rules,
and the abstract base class for custom adapters.

Публичный API для адаптации файлов навыков.

Экспортирует основной оркестратор ``Adapter``, правила адаптации по
умолчанию и абстрактный базовый класс для собственных адаптеров.
"""

from .adapter import Adapter
from .rules import DEFAULT_RULES, absAdapter

__all__ = ["Adapter", "DEFAULT_RULES", "absAdapter"]
