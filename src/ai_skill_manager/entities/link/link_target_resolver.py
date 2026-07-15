"""Resolve an OS-absolute path against the set of known skills.

Разрешение OS-absolute пути относительно набора известных скиллов.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, TYPE_CHECKING

from .link_target import SkillLinkTarget
from ...tools.path_utils import is_relative_to_resolved, same_path, normalize_path
from ..skill_kind import SkillKind

if TYPE_CHECKING:
    from ..skill_v2 import Skill


class LinkTargetResolver:
    """Finds which known skill, if any, owns a given absolute path.

    Находит, какому известному скиллу, если таковой есть, принадлежит
    заданный абсолютный путь.

    Resolution is plain path containment against each skill's own ``path``
    - the same kind of check link validation has always used - so a link
    either resolves here or is reported as unresolved; there is no
    heuristic fallback that could disagree with what materialization does
    later, because materialization consumes this same result.

    Резолюция - это простая проверка вхождения пути относительно ``path``
    каждого скилла - та же проверка, что всегда использовала валидация
    ссылок - поэтому ссылка либо резолвится здесь, либо сообщается как
    неразрешённая; эвристического запасного варианта, который мог бы
    разойтись с тем, что делает материализация позже, нет, потому что
    материализация потребляет тот же самый результат.
    """

    def resolve(self, os_absolute_path: Path, known_skills: Iterable["Skill"]) -> Optional[SkillLinkTarget]:
        """Return the ``SkillLinkTarget`` owning ``os_absolute_path``, if any.

        Возвращает ``SkillLinkTarget``, которому принадлежит
        ``os_absolute_path``, если таковой есть.
        """
        for skill in known_skills:
            if skill.kind is SkillKind.flat:
                if same_path(os_absolute_path, skill.path):
                    return SkillLinkTarget(skill_name=skill.name, relative_path=None)
                continue

            if same_path(os_absolute_path, skill.path):
                return SkillLinkTarget(skill_name=skill.name, relative_path=skill.main_file_relative_path)

            if is_relative_to_resolved(os_absolute_path, skill.path):
                relative_path = normalize_path(os_absolute_path).relative_to(normalize_path(skill.path))
                return SkillLinkTarget(skill_name=skill.name, relative_path=relative_path)

        return None
