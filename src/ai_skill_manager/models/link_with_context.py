"""Adapter-level link model.

Адаптерная модель ссылки.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from ..entities import PathLink, Skill, SkillFile, WebLink, absLink
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

    Wraps the storage-level :class:`absLink` and adds the original source location
    so the adapter can sort links and report where each link was found.

    Представляет распарсенную ссылку для обработки на уровне адаптера.
    Оборачивает :class:`absLink` уровня хранения и добавляет исходное местоположение,
    чтобы адаптер мог сортировать ссылки и сообщать, где каждая ссылка найдена.

    Attributes:
        base: Storage-level link data.
            Данные ссылки уровня хранения.
        context: Where the link was found in the source text.
            Где ссылка была найдена в исходном тексте.
    """

    base: absLink
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
    def build(skill: Skill, file: SkillFile, link: absLink) -> "LinkWithContext":
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
        if isinstance(self.base, WebLink):
            result: Path | None = None
        # EN: Path links expose the already-resolved OS path.
        # RU: Путевые ссылки отдают уже разрешённый абсолютный путь ОС.
        elif isinstance(self.base, PathLink):
            result = self.base.path.os_path
        else:
            raise ValueError(f"Unknown link type: {type(self.base)}")

        # EN: Cache the result for subsequent accesses.
        # RU: Кешируем результат для последующих обращений.
        self.__context.os_absolute_path_cache = result
        return result

    @property
    def is_link_to_skill_file(self) -> bool:
        """Return ``True`` if the link points to an existing file of the current skill.

        Возвращает ``True``, если ссылка указывает на существующий файл текущего навыка.
        """
        skill = self.context.skill
        target = self.os_absolute_path
        if target is None:
            return False

        # EN: Flat skills only accept links to their single markdown file.
        # RU: Плоские навыки принимают только ссылки на свой единственный markdown-файл.
        if skill.format.is_flat:
            return target == skill.file_path

        # EN: Directory skills accept links to any existing file under the skill folder.
        # RU: Директорийные навыки принимают ссылки на любой существующий файл внутри папки навыка.
        assert skill.folder_path is not None, "None folder path in dir skill"
        return target.is_relative_to(skill.folder_path) and target.exists()

    def is_link_to_another_skill_file(self, other_skills: List[Skill]) -> Optional[Tuple[Skill, SkillFile]]:
        """Return the other skill and SkillFile this link targets, if any.

        Возвращает другой навык и файл, на который указывает ссылка, если такой есть.
        """
        candidates = []
        for skill in other_skills:
            for file in skill.files:
                if self.os_absolute_path == file.path:
                    candidates.append((skill, file))
        if len(candidates) == 0:
            return None
        assert len(candidates) == 1, \
            f"More than 1 (skill,file) candidate for link {self.base.raw}"
        return candidates[0]

    def is_link_to_another_skill(self, other_skills: List[Skill]) -> Optional[Skill]:
        """Return the other skill this link targets, if any.

        Возвращает другой навык, на который указывает ссылка, если такой есть.
        """
        # EN: Look for a skill whose main file or folder matches the resolved
        # link path. Folder match handles repo-absolute links written without
        # the ``.md`` suffix.
        # RU: Ищем навык, основной файл или папка которого совпадает с
        # разрешённым путём ссылки. Совпадение с папкой обрабатывает
        # repo-absolute ссылки, записанные без суффикса ``.md``.
        skill_candidates = [
            skill for skill in other_skills
            if self.os_absolute_path == skill.file_path
            or (skill.folder_path is not None and self.os_absolute_path == skill.folder_path)
        ]
        if len(skill_candidates) == 0:
            return None
        assert len(skill_candidates) == 1, \
            f"More than 1 skill candidate for link {self.base.raw}"
        return skill_candidates[0]

    def target_skill(self, skills: List[Skill]) -> Optional[Skill]:
        """Return the skill whose folder contains the link target, if any.

        Возвращает навык, папка которого содержит цель ссылки, если такой есть.

        Unlike :meth:`is_link_to_another_skill`, this matches any file inside
        a skill directory, not only the skill's main file or folder itself.

        В отличие от :meth:`is_link_to_another_skill`, этот метод находит любой
        файл внутри директории скилла, а не только основной файл или саму папку.
        """
        target = self.os_absolute_path
        if target is None:
            return None
        candidates = []
        for skill in skills:
            if skill.folder_path is not None and target.is_relative_to(skill.folder_path):
                candidates.append(skill)
            elif target == skill.file_path:
                candidates.append(skill)
        if len(candidates) == 0:
            return None
        assert len(candidates) == 1, \
            f"More than 1 skill candidate for link {self.base.raw}"
        return candidates[0]

