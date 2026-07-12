"""Core adapter orchestration.

Aggregates file adapters and applies them after skills have been copied
to the target location.

Основная оркестрация адаптации.

Агрегирует адаптеры файлов и применяет их после копирования навыков
в целевое расположение.
"""

from pathlib import Path

from ..entities import Skill

from .rules import Type, absAdapter, DEFAULT_RULES, List
from .models.adapter_message import AdapterMessage
from ..validation_settings import ValidationSettings
from typing import Dict, Optional, Tuple


class Adapter:
    """Applies a set of file adapters to a copied skill.

    Ensures adapter names are unique and then runs each adapter when
    migrating from an old skill to a new skill.

    Применяет набор адаптеров файлов к скопированному навыку.

    Гарантирует уникальность имён адаптеров, а затем запускает каждый
    адаптер при миграции от старого навыка к новому.
    """

    def __init__(
        self,
        skills: List[Skill],
        adapter_list: List[Type[absAdapter]] = DEFAULT_RULES,
        skill_mapping: Optional[Dict[Skill, Skill]] = None,
        target_dir: Optional[Path] = None,
        copied_files: Optional[Dict[Path, Path]] = None,
        validation_settings: Optional[ValidationSettings] = None,
        repo_path: Optional[Path] = None,
    ):
        """Initialize the adapter with the available skills and adapter classes.

        Args:
            skills: All discovered *source* skills (before copying), used as
                context for link resolution. Resolving against the original
                source skills - rather than re-deriving identity from copied
                paths - is what lets link resolution reuse the exact same
                matching rules as validation.
                / Все обнаруженные *исходные* скиллы (до копирования),
                используемые как контекст для разрешения ссылок. Разрешение
                относительно исходных скиллов, а не повторное угадывание
                идентичности по скопированным путям, позволяет резолюции
                ссылок использовать те же самые правила сопоставления, что и
                валидация.
            adapter_list: Adapter classes to instantiate.
                / Классы адаптеров для инстанцирования.
            skill_mapping: Mapping from original source skill to its current
                location this run (a freshly copied skill, or its existing
                target-directory location if the copy was skipped). Used to
                translate a resolved source-skill identity into the path the
                link should ultimately point at.
                / Отображение исходного скилла в его текущее расположение в
                этом запуске (свежескопированный скилл или его существующее
                расположение в target, если копирование было пропущено).
                Используется, чтобы перевести разрешённую идентичность
                исходного скилла в путь, на который должна указывать ссылка.
            target_dir: Root target directory of the current sync.
                / Корневая целевая директория текущего синка.
            copied_files: Shared registry of external files already copied into
                target skills. Maps original source path -> copied path.
                / Общий реестр внешних файлов, уже скопированных в целевые
                скиллы. Отображает исходный путь -> скопированный путь.
            repo_path: Repository root of the sync destination, used to format
                repo-absolute link targets.
                / Корень репозитория целевого расположения синхронизации,
                используемый для формирования repo-absolute целей ссылок.

        Raises:
            AssertionError: If two adapters share the same name.
                / Если два адаптера имеют одинаковое имя.
        """
        # Verify unique adapter names to avoid ambiguous results.
        # Проверяем уникальность имён адаптеров, чтобы избежать неоднозначных результатов.
        adapter_names = [r.name() for r in adapter_list]
        assert len(adapter_names) == len(set(adapter_names)), (
            f"Rules must have unique names. Duplicates: "
            f"{[n for n in adapter_names if adapter_names.count(n) > 1]}"
        )

        # Build a shared context containing all skills.
        # Формируем общий контекст, содержащий все навыки.
        self.__ac = absAdapter.Context(
            skills=tuple(skills),
            skill_mapping=skill_mapping or {},
            target_dir=target_dir,
            copied_files=copied_files if copied_files is not None else {},
            validation_settings=validation_settings,
            repo_path=repo_path,
        )

        # Instantiate each adapter with the shared context.
        # Инстанцируем каждый адаптер с общим контекстом.
        self.__adapters = [adapter_cls(self.__ac)
                           for adapter_cls in adapter_list]

    @property
    def registered_adapters_name_version(self) -> List[Tuple[str, str]]:
        """Return names and versions of all registered adapters.

        Возвращает имена и версии всех зарегистрированных адаптеров.
        """
        return [(adapter.name(), adapter.version()) for adapter in self.__adapters]

    def adapt(self, old_skill: Skill, new_skill: Skill) -> Dict[str, AdapterMessage]:
        """Run all adapters on ``new_skill`` using ``old_skill`` as reference.

        Запускает все адаптеры на ``new_skill``, используя ``old_skill`` как эталон.

        Args:
            old_skill: Original skill before copying.
                / Исходный навык до копирования.
            new_skill: Copied skill in the target directory.
                / Скопированный навык в целевой директории.

        Returns:
            Mapping from adapter name to its message.
                / Отображение имени адаптера на его сообщение.
        """
        results = {}
        for adapter in self.__adapters:
            # Run the adapter and store its returned message.
            # Запускаем адаптер и сохраняем возвращённое сообщение.
            msg = adapter.adapt(old_skill, new_skill)
            results[adapter.name()] = msg
        return results
