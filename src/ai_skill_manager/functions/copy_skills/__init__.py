"""CopySkills implementations and config-name resolution.

Реализации CopySkills и разрешение имён из конфигурации.
"""

from typing import List

from .abs_copy_skills import CopySkills
from .claude_property_copy_skills import ClaudePropertyCopySkills
from .default_copy_skills import DefaultCopySkills
from .incremental_copy_skills import IncrementalCopySkills
from .orphan_removing_copy_skills import OrphanRemovingCopySkills

# Config-facing names understood by settings.target.<name>.adapters.
# "link-adapter" is the always-on baseline (plain copy + link rewriting) and
# is accepted for backward compatibility with existing configs, but no
# longer needs to be listed explicitly.
# Имена, понимаемые из конфигурации settings.target.<name>.adapters.
# "link-adapter" - всегда включённое базовое поведение (обычное копирование
# + переписывание ссылок) и принимается для обратной совместимости с
# существующими конфигурациями, но больше не обязателен для явного указания.
KNOWN_NAMES = ("link-adapter", "claude-property-adapter")


def resolve_copy_skills(names: List[str]) -> CopySkills:
    """Build the ``CopySkills`` chain for a target's configured adapter names.

    Строит цепочку ``CopySkills`` для настроенных для target'а имён
    адаптеров.

    Raises:
        ValueError: If a name is not in :data:`KNOWN_NAMES`.
            / Если имя отсутствует в :data:`KNOWN_NAMES`.
    """
    unknown = [name for name in names if name not in KNOWN_NAMES]
    if unknown:
        raise ValueError(
            f"Unknown adapter(s) {unknown}. Available adapters: {', '.join(KNOWN_NAMES)}"
        )

    copy_skills: CopySkills = DefaultCopySkills()
    if "claude-property-adapter" in names:
        copy_skills = ClaudePropertyCopySkills(copy_skills)
    return copy_skills


__all__ = [
    "CopySkills",
    "ClaudePropertyCopySkills",
    "DefaultCopySkills",
    "IncrementalCopySkills",
    "KNOWN_NAMES",
    "OrphanRemovingCopySkills",
    "resolve_copy_skills",
]
