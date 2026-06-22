"""Built-in file adaptation rules.

Exports the default adapter classes used by ``Adapter``.

Встроенные правила адаптации файлов.

Экспортирует классы адаптеров по умолчанию, используемые ``Adapter``.
"""

from typing import List, Type

from .abs_adapter import absAdapter
from .link_adapter import LinkAdapter

# Default adapters applied by Adapter.
# Адаптеры по умолчанию, применяемые Adapter.
DEFAULT_RULES: List[Type[absAdapter]] = [LinkAdapter]

__all__ = ["absAdapter", "DEFAULT_RULES", "LinkAdapter"]
