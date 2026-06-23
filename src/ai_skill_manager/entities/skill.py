"""Skill entity model.

Модель сущности навыка.
"""

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
    class Context:
        files: Optional[Tuple[SkillFile]] = None
        properties: Optional[SkillProperty] = None
        
    file_path: Path
    """absolute Path to skill main file / абсолютный путь к основному файлу навыка"""
    folder_path: Path | None
    """absolute Path to skill folder / абсолютный путь к директории навыка"""
    source_path: Path
    """absolute Path to source folder / абсолютный путь к директории источника"""
    source: Source
    format: SkillFormat  # Required skill format. / Обязательный формат навыка.
    __context: Context = field(init=False, compare=False, hash=False, default_factory=Context)
    
    def __post_init__(self):
        """Initialize derived attributes and validate paths.

        Инициализирует производные атрибуты и проверяет пути.
        """
        # EN: Validate that all stored paths have the expected shape.
        # RU: Проверяем, что все сохранённые пути имеют ожидаемый вид.
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
    def properties(self)->SkillProperty:
        """
        Skill header properties
        Свойства скила в заголовке
        """        
        if self.__context.properties is None:
            self.__context.properties = SkillProperty(self.file_path)
        return self.__context.properties
    
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
        # EN: Build the file list once and cache it inside the frozen dataclass.
        # RU: Собираем список файлов один раз и кешируем внутри замороженного dataclass.
        if self.__context.files is None:
            paths = [self.file_path]
            if self.folder_path is not None:
                # EN: For directory skills include every nested markdown file.
                # RU: Для директорийных навыков включаем все вложенные markdown-файлы.
                paths.extend(sorted(self.folder_path.rglob("*.md")))

            # EN: Deduplicate paths while preserving source order.
            # RU: Убираем дубликаты путей, сохраняя порядок следования в источнике.
            seen: set[Path] = set()
            files: list[SkillFile] = []
            for p in paths:
                if p in seen:
                    continue
                seen.add(p)
                files.append(SkillFile(p))

            self.__context.files = tuple(files)
        return self.__context.files

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
