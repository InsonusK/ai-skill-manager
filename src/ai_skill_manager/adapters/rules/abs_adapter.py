"""Base class for file adapters.

Базовый класс для адаптеров файлов.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from ..models.adapter_message import AdapterMessage
from ...entities import Skill


class absAdapter(ABC):
    """Adapts files after copying to target.

    Subclasses receive a shared ``Context`` containing all known skills
    and must implement ``adapt``.

    Адаптирует файлы после копирования в целевое расположение.

    Подклассы получают общий ``Context`` со всеми известными навыками и
    должны реализовать ``adapt``.
    """

    @dataclass(frozen=True)
    class Context:
        """Shared read-only context passed to every adapter.

        Разделяемый контекст только для чтения, передаваемый каждому адаптеру.
        """

        skills: Tuple[Skill]
        """All known skills. / Все известные навыки."""

        skill_mapping: Dict[Skill, Skill] = field(default_factory=dict)
        """Mapping from original source skill to copied target skill.

        Используется для разрешения source-ссылок, которые после копирования
        всё ещё указывают на пути в исходном источнике.
        """

    def __init__(self, adapter_context: absAdapter.Context):
        """Initialize the adapter with the shared context.

        Args:
            adapter_context: Context with all known skills.
                / Контекст со всеми известными навыками.
        """
        self._adapter_context = adapter_context
        super().__init__()

    @classmethod
    def version(cls) -> str:
        """Return the adapter version string.

        Возвращает строку версии адаптера.
        """
        return ""

    @classmethod
    def name(cls) -> str:
        """Return the adapter name, defaults to the class name.

        Возвращает имя адаптера; по умолчанию — имя класса.
        """
        return cls.__name__

    @abstractmethod
    def adapt(self, old_skill: Skill, new_skill: Skill) -> AdapterMessage:
        """Modify file(s) in place after copying.

        Изменяет файл(ы) на месте после копирования.

        Args:
            old_skill: Original skill before copying.
                / Исходный навык до копирования.
            new_skill: Copied skill in the target directory.
                / Скопированный навык в целевой директории.

        Returns:
            Message describing what the adapter changed.
                / Сообщение об изменениях, сделанных адаптером.
        """
        ...
