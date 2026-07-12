"""Sync error model.

Модель ошибки синхронизации.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class SyncError:
    """A single failure recorded while materializing a skill into staging.

    Materialization does not abort on the first failure: broken links are
    replaced with a placeholder so the rest of the skill (and the rest of
    the batch) keeps being processed, and every failure encountered is
    collected here. The whole sync still fails overall whenever this list is
    non-empty - nothing is ever silently skipped.

    Одна ошибка, зафиксированная во время материализации навыка в staging.
    Материализация не прерывается на первой ошибке: битые ссылки заменяются
    заглушкой, чтобы продолжить обработку остальной части навыка (и всей
    партии), а каждая встреченная ошибка собирается здесь. Синхронизация в
    целом всё равно завершается неудачей, если этот список не пуст — ничего
    не пропускается молча.
    """

    skill_name: str
    """Name of the skill the error occurred in. / Имя навыка, в котором произошла ошибка."""

    file: Optional[str] = None
    """Path of the file the error occurred in, relative to the skill folder
    when known. / Путь файла, в котором произошла ошибка, относительно папки
    навыка, если известен."""

    message: str = ""
    """Human-readable description of the failure. / Читаемое описание ошибки."""

    def __str__(self) -> str:
        """Return a single-line description for display."""
        location = f"{self.skill_name}/{self.file}" if self.file else self.skill_name
        return f"{location}: {self.message}"
