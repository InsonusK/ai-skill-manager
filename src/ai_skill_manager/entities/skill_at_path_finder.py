"""Resolve which skill (if any) a link target belongs to.

Определяет, к какому скиллу (если есть) относится цель ссылки.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Optional

from ..service.skill_discovery.skill.auto import AutoDiscovery
from ..tools.path_utils import same_path
from .skill_v2 import Skill

# Module logger / Логгер модуля.
logger = logging.getLogger(__name__)


class SkillAtPathFinder:
    """Finds the skill that owns a link target outside the known skill set.

    A link inside one skill can point at a file that belongs to another
    skill the current sync run hasn't loaded yet - it isn't one of the
    already discovered/known skills. This class answers "which skill, if
    any, owns this path?" by walking from the target up through its
    ancestor directories, checking each one only against itself (never its
    siblings or subtree), and stopping as soon as one of them is itself a
    skill root, or once ``repo_path`` is reached without finding one.

    Находит скилл, которому принадлежит цель ссылки, не входящая в число
    уже известных скиллов. Ссылка внутри одного скилла может указывать на
    файл, принадлежащий другому скиллу, который ещё не был загружен в
    текущем запуске синхронизации. Этот класс отвечает на вопрос "какому
    скиллу (если есть) принадлежит этот путь?", поднимаясь от цели вверх по
    родительским директориям, проверяя каждую только саму по себе (никогда
    её соседей или поддерево), и останавливаясь, как только одна из них сама
    оказывается корнем скилла, либо когда достигнут ``repo_path`` без
    результата.
    """

    def __init__(self) -> None:
        """Initialize an empty per-directory discovery cache.

        Инициализировать пустой кэш обнаружения по директориям.
        """
        self._scan_cache: Dict[Path, Optional[Skill]] = {}
        self._auto_discovery: Optional[AutoDiscovery] = None

    def find(self, path: Path, repo_path: Path) -> Optional[Skill]:
        """Return the skill that owns ``path``, searching up to ``repo_path``.

        Возвращает скилл, которому принадлежит ``path``, при поиске вплоть
        до ``repo_path``.

        Args:
            path: Link target to classify. / Цель ссылки для классификации.
            repo_path: Repo-absolute boundary; directories above it are
                never scanned. / Repo-absolute граница; директории выше неё
                никогда не сканируются.

        Returns:
            The owning :class:`Skill`, or ``None`` if none of ``path``'s
            ancestors up to and including ``repo_path`` is a skill root.
            / Скилл-владелец, либо ``None``, если ни один из предков
            ``path`` вплоть до ``repo_path`` включительно не является
            корнем скилла.

        Raises:
            ValueError: If the skill owning ``path`` itself contains a
                nested skill - a skill can't contain another skill. /
                Если скилл, которому принадлежит ``path``, сам содержит
                вложенный скилл - скилл не может содержать другой скилл.
        """
        if not path.exists():
            return None

        repo_path = repo_path.resolve()
        auto_discovery = self._get_auto_discovery(repo_path)

        # Check directory ownership first: a HumanDir skill's own main file
        # (e.g. ``foo.skill/foo.skill.md``) also matches the flat pattern by
        # name alone, so matching flat patterns first would misclassify it
        # as a *different*, standalone flat skill instead of recognizing it
        # as that directory skill's own file.
        # Сначала проверяем принадлежность директории: собственный основной
        # файл HumanDir-скилла (например, ``foo.skill/foo.skill.md``) тоже
        # совпадает с плоским паттерном по одному только имени, поэтому
        # проверка плоских паттернов в первую очередь неверно определила бы
        # его как *другой*, отдельный плоский скилл, вместо того чтобы
        # распознать в нём собственный файл этого директориального скилла.
        candidate = path if path.is_dir() else path.parent
        while True:
            skill = self._skill_rooted_at(candidate)
            if skill is not None:
                skill.repo_path = repo_path
                return skill

            if same_path(candidate, repo_path):
                break

            parent = candidate.parent
            if parent == candidate:
                logger.warning(
                    "Reached the filesystem root while looking for a skill "
                    "owning %s without hitting repo_path %s", path, repo_path
                )
                return None
            candidate = parent

        if path.is_file():
            flat_skill = auto_discovery.match_flat_file(path)
            if flat_skill is not None:
                flat_skill.repo_path = repo_path
                return flat_skill

        return None

    def _get_auto_discovery(self, repo_path: Path) -> AutoDiscovery:
        """Return the (lazily created, reused) ``AutoDiscovery`` helper."""
        if self._auto_discovery is None:
            self._auto_discovery = AutoDiscovery(scan_path=repo_path)
        return self._auto_discovery

    def _skill_rooted_at(self, directory: Path) -> Optional[Skill]:
        """Return the skill whose root is exactly ``directory``, using the cache.

        Non-recursive: only checks ``directory`` itself, never its siblings
        or subtree - except that a *matched* directory still has its own
        subtree checked for nested skills (see
        :meth:`AutoDiscovery.skill_rooted_at`).

        Возвращает скилл, корень которого - именно ``directory``, используя
        кэш. Без рекурсии: проверяет только саму ``directory``, никогда её
        соседей или поддерево - за исключением того, что у *совпавшей*
        директории всё равно проверяется её собственное поддерево на
        вложенные скиллы (см. :meth:`AutoDiscovery.skill_rooted_at`).
        """
        directory = directory.resolve()
        if directory in self._scan_cache:
            return self._scan_cache[directory]

        skill = self._auto_discovery.skill_rooted_at(directory)
        self._scan_cache[directory] = skill
        return skill
