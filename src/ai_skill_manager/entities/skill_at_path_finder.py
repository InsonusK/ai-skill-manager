"""Detect whether an arbitrary path is itself the root of a skill.

Определение того, является ли произвольный путь корнем скилла.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from ..service.discovery.skill.auto import AutoDiscovery
from .link.path_utils import same_path
from .skill_conversion import convert_legacy_skill
from .skill_v2 import Skill
from .source import LocalSource


class SkillAtPathFinder:
    """Checks whether ``path`` is exactly a skill's own file or folder.

    Проверяет, является ли ``path`` именно собственным файлом или папкой
    скилла.

    Reuses the existing pattern-matching discovery strategy, scoped to just
    ``path``'s containing directory, so a link target can be recognized as
    an unloaded skill without a full source-tree scan. Only matches when
    ``path`` itself is the skill's root (main file or folder) - it does not
    walk upward to find an ancestor skill boundary for a link to a *nested*
    file inside an unloaded skill.

    Переиспользует существующую стратегию обнаружения по паттернам,
    ограниченную директорией, содержащей ``path``, чтобы цель ссылки можно
    было распознать как незагруженный скилл без полного сканирования дерева
    источника. Совпадает только тогда, когда сам ``path`` является корнем
    скилла (основной файл или папка) - не поднимается вверх в поисках
    границы скилла-предка для ссылки на *вложенный* файл внутри
    незагруженного скилла.
    """

    def find(self, path: Path) -> Optional[Skill]:
        """Return the :class:`Skill` rooted exactly at ``path``, if any.

        Возвращает :class:`Skill`, корень которого - именно ``path``, если
        таковой есть.
        """
        if not path.exists():
            return None

        scan_root = path if path.is_dir() else path.parent
        source = LocalSource(scan_path=scan_root)
        legacy_skills = AutoDiscovery(source_path=scan_root, source=source).discover()

        for legacy in legacy_skills:
            root = legacy.folder_path if legacy.folder_path is not None else legacy.file_path
            if same_path(root, path) or same_path(legacy.file_path, path):
                return convert_legacy_skill(legacy)

        return None
