"""Adapter-level link model.

Адаптерная модель ссылки.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from ..entities import Link, LinkKind, Skill, SkillFile
from .link_location import LinkLocation

_UNSET = object()


@dataclass(frozen=True)
class LinkWithContext:
    class Context:
        """Lazy cache for the resolved OS absolute path.

        Ленивый кеш разрешённого абсолютного пути ОС.
        """

        os_absolute_path_cache: Path | None | object = _UNSET

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
    __context: Context = field(
        init=False, compare=False, hash=False, default_factory=Context
    )

    def __getattr__(self, name: str):
        """Forward attribute access to the wrapped base link.

        Перенаправляет доступ к атрибутам на обёрнутую базовую ссылку.
        """
        return getattr(self.base, name)

    def __post_init__(self):
        # EN: Ensure the wrapped link exists exactly once in the parent file.
        # RU: Убеждаемся, что обёрнутая ссылка встречается ровно один раз в родительском файле.
        link_candidates = [
            link for link in self.context.file.links if link == self.base]
        assert len(link_candidates) == 1, (
            f"Link {self.base.raw} doesn't find or has more than 1 candidate "
            f"in skill file {self.context.file.path}"
        )

    @staticmethod
    def build(skill: Skill, file: SkillFile, link: Link) -> LinkWithContext:
        """Create a :class:`LinkWithContext` from a skill, file and link.

        Создаёт :class:`LinkWithContext` из навыка, файла и ссылки.
        """
        # EN: Build the file location and wrap it together with the link.
        # RU: Собираем расположение файла и оборачиваем его вместе со ссылкой.
        lc = LinkLocation(file, skill)
        return LinkWithContext(link, lc)

    @property
    def os_absolute_path(self) -> Path | None:
        """Return the OS-absolute target path, or ``None`` for web links.

        Возвращает абсолютный путь цели ОС или ``None`` для веб-ссылок.
        The resolved path is cached on first access because ``Path.resolve()``
        performs filesystem I/O and is used repeatedly by link validation and
        adaptation logic.

        Разрешённый путь кешируется при первом обращении, так как
        ``Path.resolve()`` выполняет файловый ввод-вывод и используется
        многократно в логике валидации и адаптации ссылок.
        """
        # EN: Return the cached value if it has already been computed.
        # RU: Возвращаем закешированное значение, если оно уже вычислено.
        cached = self.__context.os_absolute_path_cache
        if cached is not _UNSET:
            return cached  # type: ignore[return-value]

        # EN: Web links have no local filesystem path.
        # RU: Веб-ссылки не имеют локального пути файловой системы.
        if self.base.kind == LinkKind.web:
            result: Path | None = None
        # EN: OS-absolute paths can be used directly.
        # RU: Абсолютные пути ОС можно использовать напрямую.
        elif self.base.kind == LinkKind.os_absolute:
            result = Path(self.base.path)
        # EN: Relative paths are resolved against the containing file's directory.
        # RU: Относительные пути разрешаются относительно директории содержащего файла.
        elif self.base.kind == LinkKind.relative:
            result = (self.context.file.path.parent / self.base.path).resolve()
        # EN: Repo-absolute paths are resolved against the repository root.
        # RU: Пути от корня репозитория разрешаются относительно корня репозитория.
        elif self.base.kind == LinkKind.repo_absolute:
            repo_path = self.context.skill.source.get_scan_location().repo_path
            result = (repo_path / self.base.path).resolve()
        else:
            raise ValueError(f"Unknown LinkKind: {self.base.kind}")

        # EN: Cache the result for subsequent accesses.
        # RU: Кешируем результат для последующих обращений.
        self.__context.os_absolute_path_cache = result
        return result

    @property
    def is_link_to_skill_file(self) -> bool:
        """Return ``True`` if the link points inside the current skill.

        Возвращает ``True``, если ссылка указывает внутрь текущего навыка.
        """
        # EN: Flat skills only accept links to their single markdown file.
        # RU: Плоские навыки принимают только ссылки на свой единственный markdown-файл.
        if self.context.skill.format.is_flat:
            return self.os_absolute_path == self.context.skill.file_path

        # EN: Non-directory formats cannot be skill-internal links.
        # RU: Недиректорийные форматы не могут быть внутри-скилловыми ссылками.
        if not self.context.skill.format.is_dir:
            return False

        assert self.context.skill.folder_path is not None, "None folder path in dir skill"

        # EN: Directory skills accept links anywhere under the skill folder.
        # RU: Директорийные навыки принимают ссылки внутри папки навыка.
        return self.os_absolute_path.is_relative_to(self.context.skill.folder_path)

    def is_link_to_another_skill_file(self, other_skills: List[Skill]) -> Optional[Tuple[Skill,SkillFile]]:
        """Return the other skill and SkillFile this link targets, if any.

        Возвращает другой навык и файл, на который указывает ссылка, если такой есть.
        """
        candidates = []
        for skill in other_skills:
            for file in skill.files:
                if self.os_absolute_path == file.path:
                    candidates.append((skill,file))
        if len(candidates) == 0:
            return None
        assert len(candidates) == 1, \
            f"More than 1 (skill,file) candidate for link {self.base.raw}"
        return candidates[0]
    
    def is_link_to_another_skill(self, other_skills: List[Skill]) -> Optional[Skill]:
        """Return the other skill this link targets, if any.

        Возвращает другой навык, на который указывает ссылка, если такой есть.
        """
        # EN: Look for a skill whose main file matches the resolved link path.
        # RU: Ищем навык, основной файл которого совпадает с разрешённым путем ссылки.
        skill_candidates = [
            skill for skill in other_skills if self.os_absolute_path == skill.file_path]
        if len(skill_candidates) == 0:
            return None
        assert len(skill_candidates) == 1, \
            f"More than 1 skill candidate for link {self.base.raw}"
        return skill_candidates[0]

    def to_skill_format(self, other_skills: List[Skill]) -> str:
        """Convert the link to the normalized skill format.

        Преобразует ссылку в нормализованный формат навыка.
        """
        # EN: Web links are kept unchanged.
        # RU: Веб-ссылки оставляем без изменений.
        if self.base.kind == LinkKind.web:
            return self.base.path

        # EN: Links inside the same skill are rewritten relative to the skill folder.
        # RU: Ссылки внутри того же навыка переписываются относительно папки навыка.
        if self.is_link_to_skill_file:
            if self.context.skill.format.is_flat:
                return "./SKILL.md"
            return f"./{self.os_absolute_path.relative_to(self.context.skill.folder_path)}"

        # EN: Links to another skill use the ``skill:<name>`` notation.
        # RU: Ссылки на другой навык используют нотацию ``skill:<name>``.
        skill = self.is_link_to_another_skill(other_skills)
        if skill is not None:
            return f"skill:{skill.properties.name}"

        raise ValueError("Invalid link format")
