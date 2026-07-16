"""Resolve an OS-absolute path against the set of known skills.

Разрешение OS-absolute пути относительно набора известных скиллов.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, TYPE_CHECKING

from ...entities.link.link_target import SkillLinkTarget
from ...entities.skill_kind import SkillKind
from ...tools.path_utils import is_relative_to_resolved, normalize_path, same_path

if TYPE_CHECKING:
    from ...entities.skill_v2 import Skill


class LinkTargetResolver:
    """Finds which known skill, if any, owns a given absolute path.

    Находит, какому известному скиллу, если таковой есть, принадлежит
    заданный абсолютный путь.

    Resolution is plain path containment against each skill's own ``path``
    - the same kind of check link validation has always used - so a link
    either resolves here or is reported as unresolved; there is no
    heuristic fallback that could disagree with what materialization does
    later, because materialization consumes this same result.

    ``resolve`` builds a ``{normalized skill.path: skill}`` index over the
    full known-skill set once per distinct ``known_skills`` object (cached
    by identity, since a run's skill dict is replaced rather than mutated
    whenever skills are added), then, for each lookup, walks from the
    target up through its own ancestor directories doing O(1) index
    lookups - instead of scanning every known skill per link, which used to
    make link resolution O(links x skills).

    Резолюция - это простая проверка вхождения пути относительно ``path``
    каждого скилла - та же проверка, что всегда использовала валидация
    ссылок - поэтому ссылка либо резолвится здесь, либо сообщается как
    неразрешённая; эвристического запасного варианта, который мог бы
    разойтись с тем, что делает материализация позже, нет, потому что
    материализация потребляет тот же самый результат.

    ``resolve`` строит индекс ``{нормализованный skill.path: skill}`` по
    всему набору известных скиллов один раз на отдельный объект
    ``known_skills`` (кэшируется по идентичности, так как словарь скиллов
    запуска заменяется, а не мутируется при добавлении скиллов), а затем
    для каждого поиска поднимается от цели вверх по её собственным
    родительским директориям, выполняя O(1) обращения к индексу - вместо
    сканирования каждого известного скилла на каждую ссылку, из-за чего
    резолюция ссылок раньше была O(ссылки x скиллы).
    """

    def __init__(self) -> None:
        """Initialize with an empty, not-yet-built index cache."""
        self._index_source: Optional[Dict[str, "Skill"]] = None
        self._index: Dict[Path, "Skill"] = {}

    def resolve(self, os_absolute_path: Path, known_skills: Dict[str, "Skill"]) -> Optional[SkillLinkTarget]:
        """Return the ``SkillLinkTarget`` owning ``os_absolute_path``, if any.

        Возвращает ``SkillLinkTarget``, которому принадлежит
        ``os_absolute_path``, если таковой есть.
        """
        index = self._get_index(known_skills)
        normalized_target = normalize_path(os_absolute_path)

        skill = index.get(normalized_target)
        if skill is not None:
            return self._exact_match_target(skill)

        # A flat skill is a single file, so it can only ever be matched
        # exactly (handled above) - only directory skills can own a path
        # nested below their own root.
        candidate = normalized_target.parent
        while True:
            skill = index.get(candidate)
            if skill is not None and skill.kind is not SkillKind.flat:
                return SkillLinkTarget(
                    skill_name=skill.name,
                    relative_path=normalized_target.relative_to(candidate),
                )
            parent = candidate.parent
            if parent == candidate:
                return None
            candidate = parent

    def resolve_one(self, os_absolute_path: Path, skill: "Skill") -> Optional[SkillLinkTarget]:
        """Return the ``SkillLinkTarget`` if ``os_absolute_path`` is owned by ``skill``.

        Unlike :meth:`resolve`, this checks a single skill directly and
        doesn't touch the index - meant for the one-off case of a skill
        just discovered via :class:`SkillAtPathFinder`, not yet part of the
        known-skill set.

        Возвращает ``SkillLinkTarget``, если ``os_absolute_path`` принадлежит
        ``skill``. В отличие от :meth:`resolve`, проверяет один скилл
        напрямую и не трогает индекс - предназначен для разового случая
        скилла, только что обнаруженного через :class:`SkillAtPathFinder` и
        ещё не входящего в набор известных скиллов.
        """
        if skill.kind is SkillKind.flat:
            if same_path(os_absolute_path, skill.path):
                return SkillLinkTarget(skill_name=skill.name, relative_path=None)
            return None

        if same_path(os_absolute_path, skill.path):
            return self._exact_match_target(skill)

        if is_relative_to_resolved(os_absolute_path, skill.path):
            relative_path = normalize_path(os_absolute_path).relative_to(normalize_path(skill.path))
            return SkillLinkTarget(skill_name=skill.name, relative_path=relative_path)

        return None

    def _get_index(self, known_skills: Dict[str, "Skill"]) -> Dict[Path, "Skill"]:
        """Return the cached ``{normalized path: skill}`` index, rebuilding on change.

        Compares against a kept reference to the previous ``known_skills``,
        not a bare ``id()`` - an id alone can be recycled once its object is
        garbage-collected, which would make a genuinely new dict look like
        a cache hit by coincidence.

        Возвращает кэшированный индекс ``{нормализованный путь: skill}``,
        перестраивая его при изменении. Сравнивает с сохранённой ссылкой на
        предыдущий ``known_skills``, а не с голым ``id()`` - id сам по себе
        может быть переиспользован после сборки мусора его объекта, из-за
        чего действительно новый словарь по случайности выглядел бы как
        попадание в кэш.
        """
        if self._index_source is not known_skills:
            self._index = {normalize_path(skill.path): skill for skill in known_skills.values()}
            self._index_source = known_skills
        return self._index

    @staticmethod
    def _exact_match_target(skill: "Skill") -> SkillLinkTarget:
        """Return the target for a path that is exactly ``skill``'s own root."""
        if skill.kind is SkillKind.flat:
            return SkillLinkTarget(skill_name=skill.name, relative_path=None)
        return SkillLinkTarget(skill_name=skill.name, relative_path=skill.main_file_relative_path)
