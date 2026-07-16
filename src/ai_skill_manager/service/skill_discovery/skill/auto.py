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

import logging
from pathlib import Path
from typing import List, Optional, Tuple

from ....entities.skill_v2 import Skill
from ....entities.source import Source
from ....entities.source.local import LocalSource
from ....models import Result
from .templates import AgentTemplate, HumanDirPattern, HumanFlatPattern, absSkillTemplate

# Module logger / Логгер модуля.
logger = logging.getLogger(__name__)


class AutoDiscovery:
    """Recursively auto-detect skills of any supported format.

    Рекурсивно автоматически обнаруживает навыки любого поддерживаемого формата.

    The only discovery strategy in use, so it is a plain concrete class
    rather than an implementation of a strategy abstraction.

    Единственная используемая стратегия обнаружения, поэтому это простой
    конкретный класс, а не реализация абстракции стратегии.
    """

    # Flat patterns are applied to files directly inside a scanned directory.
    # Плоские паттерны применяются к файлам непосредственно внутри сканируемой директории.
    _FLAT_PATTERNS: List[absSkillTemplate] = [HumanFlatPattern()]

    # Directory patterns are applied to the directory itself.
    # Директориальные паттерны применяются к самой директории.
    _DIR_PATTERNS: List[absSkillTemplate] = [AgentTemplate(), HumanDirPattern()]

    def __init__(self, scan_path: Path, source: Optional[Source] = None):
        """Initialize auto-discovery.

        Инициализировать автообнаружение.

        Args:
            scan_path: Path to scan. / Путь для сканирования.
            source: Optional source metadata, used only for its
                ``skip_folder`` setting; defaults to a plain LocalSource for
                ``scan_path``. / Опциональные метаданные источника,
                используются только для настройки ``skip_folder``; по
                умолчанию LocalSource для ``scan_path``.
        """
        if not scan_path.exists():
            # Log missing source but keep the path for downstream handling.
            # Логируем отсутствующий источник, но сохраняем путь для дальнейшей обработки.
            logger.error("scan_path not found: %s", scan_path)
        # Store the absolute path to avoid ambiguity during scanning.
        # Сохраняем абсолютный путь, чтобы избежать неоднозначности при сканировании.
        self.scan_path = scan_path.resolve()

        source = source if source is not None else LocalSource(scan_paths=(self.scan_path,))
        self._skip_folders: Tuple[str, ...] = getattr(source, "skip_folder", ("examples",))
        self._errors: List[str] = []

        flat_descs = "\n".join(f"- {p.pattern_description}" for p in self._FLAT_PATTERNS)
        dir_descs = "\n".join(f"- {p.pattern_description}" for p in self._DIR_PATTERNS)
        logger.debug(
            "AutoDiscovery initialized for %s with %d flat and %d directory pattern(s)\n"
            "flat:\n%s\n"
            "directory:\n%s",
            self.scan_path,
            len(self._FLAT_PATTERNS),
            len(self._DIR_PATTERNS),
            flat_descs,
            dir_descs,
        )

    def discover(self) -> Result[List[Skill]]:
        """Recursively discover all skills at the source path.

        Рекурсивно обнаружить все навыки по пути источника.

        Returns:
            The discovered skills and any per-candidate errors (e.g. a
            missing frontmatter name) collected while scanning. /
            Обнаруженные скиллы и любые ошибки по кандидатам (например,
            отсутствующее имя во frontmatter), собранные при сканировании.
        """
        logger.debug("Starting discovery at %s", self.scan_path)
        self._errors = []
        if not self.scan_path.exists():
            # Missing source produces an empty result; the base class logs the error.
            # Отсутствующий источник даёт пустой результат; базовый класс логирует ошибку.
            logger.debug("Source path does not exist: %s", self.scan_path)
            return Result([], [])

        if self.scan_path.is_file():
            # A file can only match flat patterns.
            # Файл может соответствовать только плоским паттернам.
            logger.debug("Source path is a file, matching flat patterns only")
            return Result(self._handle_file(self.scan_path), self._errors)

        # Directories are scanned recursively for both flat and directory patterns.
        # Директории сканируются рекурсивно на предмет плоских и директориальных паттернов.
        logger.debug("Source path is a directory, scanning recursively")
        return Result(self._scan_directory(self.scan_path), self._errors)

    def _match_flat_patterns(self, path: Path) -> List[Tuple[Skill, absSkillTemplate]]:
        """Return all flat-pattern matches for a file path.

        Вернуть все совпадения по плоским паттернам для пути к файлу.

        A pattern that raises (e.g. a missing frontmatter name) is collected
        as an error and treated as not matching, rather than aborting the
        whole scan.

        Паттерн, вызвавший исключение (например, отсутствующее имя во
        frontmatter), собирается как ошибка и считается несовпавшим, вместо
        прерывания всего сканирования.

        Args:
            path: File path to check. / Путь к файлу для проверки.

        Returns:
            List of (matching flat skill, pattern) pairs. / Список пар
            (совпавший плоский скилл, паттерн).
        """
        matches: List[Tuple[Skill, absSkillTemplate]] = []
        for pattern in self._FLAT_PATTERNS:
            try:
                skill = pattern.match(path)
            except ValueError as exc:
                self._errors.append(str(exc))
                continue
            if skill is not None:
                matches.append((skill, pattern))
        return matches

    def _match_directory_patterns(self, path: Path) -> List[Tuple[Skill, absSkillTemplate]]:
        """Return all directory-pattern matches for a directory path.

        Вернуть все совпадения по директориальным паттернам для пути к директории.

        A pattern that raises (e.g. a missing frontmatter name) is collected
        as an error and treated as not matching, rather than aborting the
        whole scan.

        Паттерн, вызвавший исключение (например, отсутствующее имя во
        frontmatter), собирается как ошибка и считается несовпавшим, вместо
        прерывания всего сканирования.

        Args:
            path: Directory path to check. / Путь к директории для проверки.

        Returns:
            List of (matching directory skill, pattern) pairs. / Список пар
            (совпавший директориальный скилл, паттерн).
        """
        matches: List[Tuple[Skill, absSkillTemplate]] = []
        for pattern in self._DIR_PATTERNS:
            try:
                skill = pattern.match(path)
            except ValueError as exc:
                self._errors.append(str(exc))
                continue
            if skill is not None:
                matches.append((skill, pattern))
        return matches

    def match_flat_file(self, path: Path) -> Optional[Skill]:
        """Return the skill if ``path`` itself matches a flat pattern.

        Non-recursive: only checks ``path`` itself against the registered
        flat patterns (e.g. ``*.skill.md``).

        Возвращает скилл, если сам ``path`` совпадает с плоским паттерном.
        Без рекурсии: проверяет только сам ``path`` по зарегистрированным
        плоским паттернам (например, ``*.skill.md``).

        Raises:
            ValueError: If ``path`` matches more than one flat pattern.
                / Если ``path`` совпадает более чем с одним плоским паттерном.
        """
        matches = self._handle_file(path)
        return matches[0] if matches else None

    def skill_rooted_at(self, directory: Path) -> Optional[Skill]:
        """Return the skill whose root is exactly ``directory``, without recursing.

        Checks only whether ``directory`` itself matches a directory
        pattern, reconciled against flat-pattern matches on its direct
        child files - it never looks at subdirectory content beyond that
        (siblings and nested directories are not scanned to answer this
        question). If ``directory`` does match, its subtree is still
        checked for nested skills, since a skill cannot contain another
        skill.

        Возвращает скилл, корень которого - именно ``directory``, без
        рекурсии. Проверяет только совпадение самой ``directory`` с
        директориальным паттерном, согласованное с плоскими совпадениями её
        непосредственных дочерних файлов - не заглядывает в содержимое
        поддиректорий сверх этого (соседние и вложенные директории не
        сканируются ради ответа на этот вопрос). Если ``directory``
        совпадает, её поддерево всё равно проверяется на вложенные скиллы,
        так как скилл не может содержать другой скилл.

        Raises:
            ValueError: On ambiguous/conflicting directory definitions, or
                nested skills inside the matched directory. / При
                неоднозначных/конфликтующих определениях директории, либо
                при вложенных скиллах внутри совпавшей директории.
        """
        dir_matches = self._match_directory_patterns(directory)
        if not dir_matches:
            return None

        if len(dir_matches) > 1:
            # Multiple directory patterns matched (e.g. SKILL.md + {dir}.skill.md).
            # Совпало несколько директориальных паттернов (например, SKILL.md + {dir}.skill.md).
            raise ValueError(
                f"Skill definition conflict in directory: {directory}.\n"
                f"Candidates: {[pattern.pattern_description for _, pattern in dir_matches]}"
            )

        dir_skill, _ = dir_matches[0]
        dir_main_file = dir_skill.path / dir_skill.main_file_relative_path

        flat_matches = self._flat_matches_in(directory)

        if not flat_matches:
            # Directory skill with no flat files: ensure it has no nested skills.
            # Директориальный навык без плоских файлов: убедиться, что нет вложенных навыков.
            self._ensure_no_nested_skills(directory, dir_main_file)
            return dir_skill

        if len(flat_matches) == 1:
            flat_skill = flat_matches[0]
            if dir_main_file.resolve() == flat_skill.path.resolve():
                # The single flat file is the same as the directory skill marker
                # (e.g. {dir}.skill.md for HumanDir). Treat it as a directory skill.
                # Единственный плоский файл совпадает с маркером директориального навыка
                # (например, {dir}.skill.md для HumanDir). Считаем директориальным навыком.
                self._ensure_no_nested_skills(directory, dir_main_file)
                return dir_skill

            # One directory pattern and a different flat file: ambiguous.
            # Один директориальный паттерн и другой плоский файл: неоднозначность.
            raise ValueError(
                f"Cannot unambiguously determine skill in directory: {directory}\n"
                f".Candidates\n1. {dir_main_file}\n2. {flat_skill.path}"
            )

        # One directory pattern plus multiple flat files: conflict.
        # Один директориальный паттерн плюс несколько плоских файлов: конфликт.
        raise ValueError(
            f"Skill definition conflict in directory: {directory}")

    def _flat_matches_in(self, directory: Path) -> List[Skill]:
        """Return flat-pattern matches among ``directory``'s direct child files.

        Non-recursive: only looks at files directly inside ``directory``,
        not its subdirectories.

        Возвращает совпадения по плоским паттернам среди непосредственных
        дочерних файлов ``directory``. Без рекурсии: рассматривает только
        файлы непосредственно внутри ``directory``, не её поддиректории.
        """
        flat_matches: List[Skill] = []
        for file_path in sorted(directory.iterdir()):
            if file_path.is_file():
                flat_matches.extend(self._handle_file(file_path))
        return flat_matches

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
        logger.debug("Checking file for flat patterns: %s", filepath)
        matches = self._match_flat_patterns(filepath)
        logger.debug("Flat pattern matches for %s: %d", filepath, len(matches))

        if not matches:
            return []
        if len(matches) == 1:
            return [matches[0][0]]

        # More than one flat pattern matched: the file's format is ambiguous.
        # Совпало более одного плоского паттерна: формат файла неоднозначен.
        raise ValueError(
            f"Skill definition conflict inFile {filepath}.\n"
            f"Candidates: {[pattern.pattern_description for _, pattern in matches]}"
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
        logger.debug("Scanning directory: %s", directory)

        # Check whether the directory itself is a directory skill root first,
        # so a match never triggers a redundant recursive scan of its subtree.
        # Сначала проверяем, является ли сама директория корнем
        # директориального навыка, чтобы совпадение не запускало избыточное
        # рекурсивное сканирование её поддерева.
        dir_skill = self.skill_rooted_at(directory)
        if dir_skill is not None:
            logger.debug("Directory skill matched at %s", directory)
            return [dir_skill]

        # No directory skill here: collect flat files and recurse into subdirs.
        # Здесь нет директориального навыка: собираем плоские файлы и рекурсия в поддиректории.
        flat_matches = self._flat_matches_in(directory)

        logger.debug(
            "Directory %s: %d flat match(es), no directory pattern match",
            directory,
            len(flat_matches),
        )
        results = list(flat_matches)
        logger.debug("No directory skill in %s, recursing into subdirectories", directory)
        results.extend(self._recurse_subdirectories(directory))
        return results

    def _recurse_subdirectories(self, directory: Path) -> List[Skill]:
        """Scan all subdirectories recursively.

        Рекурсивно просканировать все поддиректории.

        Args:
            directory: Parent directory. / Родительская директория.

        Returns:
            Skills discovered in subdirectories. / Навыки, обнаруженные в поддиректориях.
        """
        results: List[Skill] = []
        subdirs = [subdir for subdir in sorted(directory.iterdir()) if subdir.is_dir()]
        logger.debug("Recursing into %d subdirectory(ies) of %s", len(subdirs), directory)
        for subdir in subdirs:
            results.extend(self._scan_directory(subdir))
        return results

    def _is_under_skip_folder(self, directory: Path, path: Path) -> bool:
        """Return ``True`` if ``path`` is inside a skipped subdirectory.

        Возвращает ``True``, если ``path`` находится внутри пропускаемой
        поддиректории.
        """
        try:
            first_part = path.relative_to(directory).parts[0]
        except (ValueError, IndexError):
            return False
        return first_part in self._skip_folders

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
        logger.debug("Checking for nested skills inside %s", directory)
        main_file_resolved = main_file.resolve()
        for path in directory.rglob("*"):
            if path == directory:
                continue

            if self._is_under_skip_folder(directory, path):
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
