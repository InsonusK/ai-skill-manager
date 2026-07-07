"""Built-in file adaptation rules.

Exports the default adapter classes used by ``Adapter``.

Встроенные правила адаптации файлов.

Экспортирует классы адаптеров по умолчанию, используемые ``Adapter``.
"""

from typing import Dict, List, Type

from .abs_adapter import absAdapter
from .link_adapter import LinkAdapter
from .claude_property_adapter import ClaudePropertyAdapter

# Default adapters applied by Adapter.
# Адаптеры по умолчанию, применяемые Adapter.
DEFAULT_RULES: List[Type[absAdapter]] = [LinkAdapter]

# Config-facing name -> adapter class registry.
# Реестр имя-в-конфиге -> класс адаптера.
REGISTRY: Dict[str, Type[absAdapter]] = {
    "link-adapter": LinkAdapter,
    "claude-property-adapter": ClaudePropertyAdapter,
}


def resolve_adapters(names: List[str]) -> List[Type[absAdapter]]:
    """Resolve config adapter names into adapter classes.

    Разрешает имена адаптеров из конфига в классы адаптеров.

    Raises:
        ValueError: If a name is not present in :data:`REGISTRY`.
            / Если имя отсутствует в :data:`REGISTRY`.
    """
    resolved: List[Type[absAdapter]] = []
    for name in names:
        adapter_cls = REGISTRY.get(name)
        if adapter_cls is None:
            raise ValueError(
                f"Unknown adapter '{name}'. Available adapters: "
                f"{', '.join(sorted(REGISTRY))}"
            )
        resolved.append(adapter_cls)
    return resolved


__all__ = [
    "absAdapter",
    "DEFAULT_RULES",
    "LinkAdapter",
    "ClaudePropertyAdapter",
    "REGISTRY",
    "resolve_adapters",
]
