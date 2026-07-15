"""Build one skill's file list - implements step 2.

Only finds and classifies a skill's own files. Enriching markdown files
with links is a separate concern (``LinkDiscovery``), invoked by the
orchestrator (``SyncCommand``), not by this unit.

Строит список файлов одного скилла - реализует шаг 2.

Только находит и классифицирует собственные файлы скилла. Обогащение
markdown-файлов ссылками - отдельная забота (``LinkDiscovery``), вызываемая
оркестратором (``SyncCommand``), а не этим юнитом.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ..entities.skill_file_v2 import MarkdownSkillFile, SkillFile
from ..entities.skill_kind import SkillKind

if TYPE_CHECKING:
    from ..entities.skill_v2 import Skill


class FileDiscovery:
    """Populates one skill's ``files`` - implements step 2.

    Заполняет ``files`` одного скилла - реализует шаг 2.
    """

    def discover(self, skill: "Skill") -> None:
        """Populate ``skill.files`` in place with its own files.

        Заполняет ``skill.files`` на месте его собственными файлами.

        Markdown files are classified as ``MarkdownSkillFile`` (with an
        empty ``links`` list, filled in later) so ``LinkDiscovery`` has
        somewhere to attach resolved links.

        Markdown-файлы классифицируются как ``MarkdownSkillFile`` (с
        пустым списком ``links``, заполняемым позже), чтобы
        ``LinkDiscovery`` было куда прикрепить разрешённые ссылки.
        """
        if skill.kind is SkillKind.flat:
            skill.files.append(MarkdownSkillFile(name=skill.path.name, path=Path(".")))
            return

        for candidate in sorted(skill.path.rglob("*")):
            if not candidate.is_file():
                continue
            relative_path = candidate.relative_to(skill.path)
            if candidate.suffix.lower() == ".md":
                skill.files.append(MarkdownSkillFile(name=candidate.name, path=relative_path))
            else:
                skill.files.append(SkillFile(name=candidate.name, path=relative_path))
