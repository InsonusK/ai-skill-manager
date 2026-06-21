from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple
from .skill_file import SkillFile
from .skill_format import SkillFormat
from .skill_propetry import SkillProperty
from .source.source import Source


@dataclass(frozen=True)
class Skill:
    """Represents a discovered skill on disk.

    Представляет обнаруженный навык на диске.
    """

    file_path: Path
    """absolute Path to skill main file"""
    folder_path: Path | None
    """absolute Path to skill folder"""
    source_path: Path
    """absolute Path to source folder"""
    source: Source
    format: SkillFormat  # Required skill format. / Обязательный формат навыка.
    properties: SkillProperty = field(init=False)
    _files: Tuple[SkillFile] = field(
        default=None, init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self):
        # Обход frozen через object.__setattr__
        object.__setattr__(self, "properties", SkillProperty(self.file_path))
        assert self.file_path.is_absolute(
        ), f"File_path must be absolute format. Current value: {self.file_path}"
        assert self.file_path.is_file(
        ), f"File_path must lead to file. Now it leads to {self.file_path}"
        if self.format.is_dir:
            assert self.folder_path.is_absolute(
            ), f"Folder_path must be absolute format. Current value: {self.folder_path}"
            assert self.folder_path.is_dir(
            ), f"Folder_path must lead to folder. Now it leads to {self.folder_path}"
        assert self.source_path.is_absolute(
        ), f"SourceSpath must be in absolute format. Current value: {self.source_path}"
        assert self.source_path.is_dir(
        ), f"Source_path must lead to folder. Now it leads to {self.source_path}"

    @property
    def name(self) -> Optional[str]:
        """Return the skill name from frontmatter, if present.

        Вернуть имя скилла из frontmatter, если оно есть.
        """
        return self.properties.name

    @property
    def files(self) -> Tuple[SkillFile]:
        """Return all markdown files that belong to this skill.

        Вернуть все markdown-файлы, принадлежащие этому скиллу.

        The result is cached. For flat skills this is only the skill markdown
        file; for directory skills it also includes all nested ``*.md`` files.

        Результат кешируется. Для плоских скиллов это только markdown-файл
        скилла; для директорий также включаются все вложенные ``*.md`` файлы.
        """
        if self._files is None:
            paths = [self.file_path]
            if self.folder_path is not None:
                paths.extend(sorted(self.folder_path.rglob("*.md")))

            seen: set[Path] = set()
            files: list[SkillFile] = []
            for p in paths:
                if p in seen:
                    continue
                seen.add(p)
                files.append(SkillFile(p))

            object.__setattr__(self, "_files", tuple(files))
        return self._files

    def is_flat(self) -> bool:
        """Return ``True`` if the skill is a single markdown file.

        Возвращает ``True``, если скилл представлен одним markdown-файлом.
        """
        return self.folder_path is None

    def is_dir(self) -> bool:
        """Return ``True`` if the skill is a directory.

        Возвращает ``True``, если скилл представлен директорией.
        """
        return not self.is_flat()
