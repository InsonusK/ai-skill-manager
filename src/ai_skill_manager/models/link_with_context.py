"""A parsed link plus the file it was found in.

Разобранная ссылка вместе с файлом, в котором она найдена.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..entities.link import LinkData


@dataclass(frozen=True)
class LinkWithContext:
    """Wraps raw :class:`LinkData` with its owning file's location.

    Used only by link exclude rules (inline-code/web-link/skip-folder), which
    need the containing file's path and content to decide whether a link
    should be skipped - not the resolved target. Exclude rules run before
    classification, so this always wraps the raw parse result, never a
    classified :class:`~ai_skill_manager.entities.link.abs_link.absLink`.

    Оборачивает сырой :class:`LinkData` с расположением его владеющего
    файла. Используется только правилами исключения ссылок
    (инлайн-код/веб-ссылка/пропускаемая директория), которым для решения,
    пропустить ли ссылку, нужны путь и содержимое содержащего файла, а не
    разрешённая цель. Правила исключения выполняются до классификации,
    поэтому здесь всегда оборачивается сырой результат разбора, а не
    классифицированный :class:`~ai_skill_manager.entities.link.abs_link.absLink`.

    Attributes:
        base: Raw link data. / Сырые данные ссылки.
        file_path: Absolute path of the file containing the link.
            Абсолютный путь файла, содержащего ссылку.
        content: Full text content of the file containing the link.
            Полное текстовое содержимое файла, содержащего ссылку.
    """

    base: LinkData
    file_path: Path
    content: str

    def __getattr__(self, name: str):
        """Forward attribute access to the wrapped base link.

        Перенаправляет доступ к атрибутам на обёрнутую базовую ссылку.
        """
        return getattr(self.base, name)

    @staticmethod
    def build(file_path: Path, content: str, link: LinkData) -> "LinkWithContext":
        """Create a :class:`LinkWithContext` from a file location and a link.

        Создаёт :class:`LinkWithContext` из расположения файла и ссылки.
        """
        return LinkWithContext(link, file_path, content)
