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
from typing import List, TYPE_CHECKING

from ..entities.skill_file_v2 import MarkdownSkillFile, SkillFile
from ..entities.skill_kind import SkillKind

if TYPE_CHECKING:
    from ..entities.skill_v2 import Skill


def discover(skill: "Skill") -> List[SkillFile]:
    """Return ``skill``'s own files, classified but not link-enriched.

    Возвращает собственные файлы ``skill``, классифицированные, но ещё не
    обогащённые ссылками.

    Markdown files are classified as ``MarkdownSkillFile`` (with an empty
    ``links`` list, filled in later) so ``LinkDiscovery`` has somewhere to
    attach resolved links. Does not touch ``skill.files`` - the caller
    decides what to do with the result.

    Markdown-файлы классифицируются как ``MarkdownSkillFile`` (с пустым
    списком ``links``, заполняемым позже), чтобы ``LinkDiscovery`` было
    куда прикрепить разрешённые ссылки. Не трогает ``skill.files`` -
    вызывающая сторона сама решает, что делать с результатом.
    """
    if skill.kind is SkillKind.flat:
        return [MarkdownSkillFile(name=skill.path.name, path=Path("."))]

    files: List[SkillFile] = []
    for candidate in sorted(skill.path.rglob("*")):
        if not candidate.is_file():
            continue
        relative_path = candidate.relative_to(skill.path)
        if candidate.suffix.lower() == ".md":
            files.append(MarkdownSkillFile(name=candidate.name, path=relative_path))
        else:
            files.append(SkillFile(name=candidate.name, path=relative_path))
    return files
