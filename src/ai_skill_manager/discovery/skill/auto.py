"""Auto-discovery strategy.

Recursively scans a path (file or directory) and detects skills according to
registered flat and directory patterns.

Стратегия автообнаружения.
Рекурсивно сканирует путь (файл или директорию) и обнаруживает навыки
в соответствии с зарегистрированными плоскими и директориальными паттернами.

Flat patterns (detected on files):
Плоские паттерны (обнаруживаются на файлах):
- HumanFlat: ``*.skill.md``

Directory patterns (detected on directories):
Директориальные паттерны (обнаруживаются на директориях):
- Agent: directory contains ``SKILL.md``
- HumanDir: directory contains ``{dir_name}.skill.md``
"""

from pathlib import Path
from typing import List, Optional

from ...entities import Skill, Source
from ...entities.source import LocalSource
from .base import AgentPattern, HumanDirPattern, HumanFlatPattern, SkillPattern
from .abs_discovery_strategy import absDiscoveryStrategy


class AutoDiscovery(absDiscoveryStrategy):
    """Recursively auto-detect skills of any supported format.

    Рекурсивно автоматически обнаруживает навыки любого поддерживаемого формата.
    """

    # Flat patterns are applied to files directly inside a scanned directory.
    # Плоские паттерны применяются к файлам непосредственно внутри сканируемой директории.
    _FLAT_PATTERNS: List[SkillPattern] = [HumanFlatPattern]

    # Directory patterns are applied to the directory itself.
    # Директориальные паттерны применяются к самой директории.
    _DIR_PATTERNS: List[SkillPattern] = [AgentPattern, HumanDirPattern]

    def __init__(
        self, source_path: Path, source: Source
    ):
        """Initialize auto-discovery.

        Инициализировать автообнаружение.

        Args:
            source_path: Path to scan. / Путь для сканирования.
            source: Optional source metadata; defaults to a LocalSource for
                ``source_path``. / Опциональные метаданные источника; по
                умолчанию LocalSource для ``source_path``.
        """
        super().__init__(source_path)
        self._source = source if source is not None else LocalSource(
            self.source_path)
        
        self._flat_patterns:List[SkillPattern] = [pattern(source, source_path)
                               for pattern in self._FLAT_PATTERNS]
        self._dir_patterns:List[SkillPattern] = [pattern(source, source_path)
                              for pattern in self._DIR_PATTERNS]
        

    def discover(self) -> List[Skill]:
        """Recursively discover all skills at the source path.

        Рекурсивно обнаружить все навыки по пути источника.

        Returns:
            List of discovered skills. / Список обнаруженных навыков.
        """
        if not self.source_path.exists():
            # Missing source produces an empty result; the base class logs the error.
            # Отсутствующий источник даёт пустой результат; базовый класс логирует ошибку.
            return []

        if self.source_path.is_file():
            # A file can only match flat patterns.
            # Файл может соответствовать только плоским паттернам.
            return self._handle_file(self.source_path)

        # Directories are scanned recursively for both flat and directory patterns.
        # Директории сканируются рекурсивно на предмет плоских и директориальных паттернов.
        return self._scan_directory(self.source_path)

    def _match_flat_patterns(self, path: Path) -> List[Skill]:
        """Return all flat-pattern matches for a file path.

        Вернуть все совпадения по плоским паттернам для пути к файлу.

        Args:
            path: File path to check. / Путь к файлу для проверки.

        Returns:
            List of matching flat skills. / Список подходящих плоских навыков.
        """
        return [
            skill
            for pattern in self._flat_patterns
            if (skill := pattern.match(path)) is not None
        ]

    def _match_directory_patterns(self, path: Path) -> List[Skill]:
        """Return all directory-pattern matches for a directory path.

        Вернуть все совпадения по директориальным паттернам для пути к директории.

        Args:
            path: Directory path to check. / Путь к директории для проверки.

        Returns:
            List of matching directory skills. / Список подходящих директориальных навыков.
        """
        return [
            skill
            for pattern in self._dir_patterns
            if (skill := pattern.match(path)) is not None
        ]

    def _handle_file(self, filepath: Path) -> List[Skill]:
        """Handle a single file path.

        Обработать один путь к файлу.

        Args:
            filepath: File path to check. / Путь к файлу для проверки.

        Returns:
            Empty list, single skill, or raises on ambiguity. /
            Пустой список, один навык или ошибка при неоднозначности.

        Raises:
            ValueError: If the file matches more than one flat pattern.
            ValueError: Если файл соответствует более чем одному плоскому паттерну.
        """
        matches = self._match_flat_patterns(filepath)

        if not matches:
            return []
        if len(matches) == 1:
            return matches

        # More than one flat pattern matched: the file's format is ambiguous.
        # Совпало более одного плоского паттерна: формат файла неоднозначен.
        raise ValueError(
            f"Skill definition conflict inFile {filepath}.\n"
            f"Candidates: {[s.format.value for s in matches]}"
        )

    def _scan_directory(self, directory: Path) -> List[Skill]:
        """Recursively scan a directory for skills.

        Рекурсивно просканировать директорию на наличие навыков.

        Args:
            directory: Directory to scan. / Директория для сканирования.

        Returns:
            List of discovered skills. / Список обнаруженных навыков.

        Raises:
            ValueError: On ambiguous or conflicting skill definitions.
            ValueError: При неоднозначных или конфликтующих определениях навыков.
        """
        # Collect flat skills from files directly inside this directory.
        # Собираем плоские навыки из файлов непосредственно в этой директории.
        flat_matches: List[Skill] = []
        for file_path in sorted(directory.iterdir()):
            if file_path.is_file():
                flat_matches.extend(self._handle_file(file_path))

        # Check whether the directory itself matches a directory skill pattern.
        # Проверяем, соответствует ли сама директория паттерну директориального навыка.
        dir_matches = self._match_directory_patterns(directory)

        # No directory skill here: collect flat files and recurse into subdirs.
        # Здесь нет директориального навыка: собираем плоские файлы и рекурсия в поддиректории.
        if not dir_matches:
            results = list(flat_matches)
            results.extend(self._recurse_subdirectories(directory))
            return results

        if len(dir_matches) > 1:
            # Multiple directory patterns matched (e.g. SKILL.md + {dir}.skill.md).
            # Совпало несколько директориальных паттернов (например, SKILL.md + {dir}.skill.md).
            raise ValueError(
                f"Skill definition conflict in directory: {directory}.\n"
                f"Candidates: {[s.format.value for s in dir_matches]}"
            )

        # Exactly one directory pattern matched.
        # Совпал ровно один директориальный паттерн.
        dir_skill = dir_matches[0]

        if not flat_matches:
            # Directory skill with no flat files: ensure it has no nested skills.
            # Директориальный навык без плоских файлов: убедиться, что нет вложенных навыков.
            self._ensure_no_nested_skills(directory, dir_skill.file_path)
            return [dir_skill]

        if len(flat_matches) == 1:
            flat_skill = flat_matches[0]
            if dir_skill.file_path.resolve() == flat_skill.file_path.resolve():
                # The single flat file is the same as the directory skill marker
                # (e.g. {dir}.skill.md for HumanDir). Treat it as a directory skill.
                # Единственный плоский файл совпадает с маркером директориального навыка
                # (например, {dir}.skill.md для HumanDir). Считаем директориальным навыком.
                self._ensure_no_nested_skills(directory, dir_skill.file_path)
                return [dir_skill]

            # One directory pattern and a different flat file: ambiguous.
            # Один директориальный паттерн и другой плоский файл: неоднозначность.
            raise ValueError(
                f"Cannot unambiguously determine skill in directory: {directory}\n"
                f".Candidates\n1. {dir_skill.file_path}\n2. {flat_skill.file_path}"
            )

        # One directory pattern plus multiple flat files: conflict.
        # Один директориальный паттерн плюс несколько плоских файлов: конфликт.
        raise ValueError(
            f"Skill definition conflict in directory: {directory}")

    def _recurse_subdirectories(self, directory: Path) -> List[Skill]:
        """Scan all subdirectories recursively.

        Рекурсивно просканировать все поддиректории.

        Args:
            directory: Parent directory. / Родительская директория.

        Returns:
            Skills discovered in subdirectories. / Навыки, обнаруженные в поддиректориях.
        """
        results: List[Skill] = []
        for subdir in sorted(directory.iterdir()):
            if subdir.is_dir():
                results.extend(self._scan_directory(subdir))
        return results

    def _ensure_no_nested_skills(self, directory: Path, main_file: Path) -> None:
        """Ensure a directory skill does not contain nested skills.

        Убедиться, что директориальный навык не содержит вложенных навыков.

        Args:
            directory: Directory chosen as a skill. / Директория, выбранная в качестве навыка.
            main_file: The directory skill's main markdown file. /
                Основной markdown-файл директориального навыка.

        Raises:
            ValueError: If any nested skill pattern is found inside.
            ValueError: Если внутри найден какой-либо паттерн вложенного навыка.
        """
        main_file_resolved = main_file.resolve()
        for path in directory.rglob("*"):
            if path == directory:
                continue

            if path.is_file():
                # Any flat file other than the main file is a nested skill.
                # Любой плоский файл, кроме основного, является вложенным навыком.
                if path.resolve() != main_file_resolved and self._match_flat_patterns(path):
                    raise ValueError(
                        f"Nested skills detected in directory skill: {directory}"
                    )
            elif path.is_dir():
                # Any subdirectory matching a directory pattern is a nested skill.
                # Любая поддиректория, соответствующая директориальному паттерну,
                # является вложенным навыком.
                if self._match_directory_patterns(path):
                    raise ValueError(
                        f"Nested skills detected in directory skill: {directory}"
                    )
