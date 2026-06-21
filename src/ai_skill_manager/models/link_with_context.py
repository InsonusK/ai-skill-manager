"""Adapter-level link model.

Адаптерная модель ссылки.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from ..entities import Link, LinkKind, Skill, SkillFile
from .link_location import LinkLocation


@dataclass(frozen=True)
class LinkWithContext:
    """Represents a parsed link for adapter-level processing.

    Wraps the storage-level :class:`Link` and adds the original source location
    so the adapter can sort links and report where each link was found.

    Представляет распарсенную ссылку для обработки на уровне адаптера.
    Оборачивает :class:`Link` уровня хранения и добавляет исходное местоположение,
    чтобы адаптер мог сортировать ссылки и сообщать, где каждая ссылка найдена.

    Attributes:
        base: Storage-level link data.
            Данные ссылки уровня хранения.
        context: Where the link was found in the source text.
            Где ссылка была найдена в исходном тексте.
    """

    base: Link
    context: LinkLocation

    def __getattr__(self, name: str):
        """Forward attribute access to the wrapped base link.

        Перенаправляет доступ к атрибутам на обёрнутую базовую ссылку.
        """
        return getattr(self.base, name)

    def __post_init__(self):
        link_candidates = [
            link for link in self.context.file.links if link == self.base]
        assert len(
            link_candidates) == 0, f"Link {self.base.raw} doesn't find in skill file {self.context.file.path}"
        assert len(
            link_candidates) == 1, f"Link {self.base.raw} has more than 1 candidate in skill file {self.context.file.path}"

    @staticmethod
    def build(skill: Skill, file: SkillFile, link: Link) -> LinkWithContext:
        lc = LinkLocation(file, skill)
        return LinkWithContext(link, lc)

    @property
    def os_absolute_path(self) -> Path | None:
        if self.base.kind == LinkKind.web:
            return None
        elif self.base.kind == LinkKind.os_absolute:
            return Path(self.base.path)
        elif self.base.kind == LinkKind.relative:
            return (self.context.file.path.parent / self.base.path).resolve()
        elif self.base.kind == LinkKind.repo_absolute:
            return (self.context.skill.source_path / self.base.path).resolve()
        else:
            raise ValueError(f"Unknown LinkKind: {self.base.kind}")

    @property
    def is_link_to_skill_file(self) -> bool:
        if self.context.skill.format.is_flat:
            return self.os_absolute_path == self.context.skill.file_path

        if not self.context.skill.format.is_dir:
            return False

        assert self.context.skill.folder_path is not None, "None folder path in dir skill"

        return self.os_absolute_path.is_relative_to(self.context.skill.folder_path)

    def is_link_to_another_skill(self, other_skills: List[Skill]) -> Optional[Skill]:
        skill_candidates = [
            skill for skill in other_skills if self.os_absolute_path == skill.file_path]
        if len(skill_candidates) == 0:
            return None
        assert len(skill_candidates) > 1, \
            f"More than 1 skill candidate for link {self.base.raw}"
        return skill_candidates[0]

    @property
    def to_skill_format(self, other_skills: List[Skill]) -> str:
        if self.is_link_to_skill_file:
            return f"./{self.os_absolute_path.relative_to(self.context.skill.folder_path)}"
        if (skill := self.is_link_to_another_skill(other_skills)) is not None:
            return f"skill:{skill.properties.name}"
        raise ValueError("Invalid link format")
