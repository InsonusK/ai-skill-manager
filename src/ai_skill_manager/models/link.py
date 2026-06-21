"""Storage-level link model.

Модель ссылки на уровне хранения.
"""

from dataclasses import dataclass
from typing import Literal, Optional

from .link_kind import LinkKind


@dataclass(frozen=True)
class Link:
    """Represents a parsed link found in markdown content.

    This is the storage-level representation: it intentionally does **not**
    contain a back-reference to the owning skill or file context, so it can be
    stored inside :class:`SkillFile` without creating circular dependencies.

    Представляет распарсенную ссылку в markdown-контенте.
    Это представление уровня хранения: она намеренно не содержит обратной
    ссылки на владеющий скилл или контекст файла, поэтому может храниться
    внутри :class:`SkillFile` без создания циклических зависимостей.

    Attributes:
        raw: The exact link text as it appears in the source.
            Точный текст ссылки в исходнике.
        path: The link target path without the URL fragment.
            Путь цели ссылки без фрагмента URL.
        text: The display text of the link.
            Отображаемый текст ссылки.
        kind: Whether the link is an OS absolute, repo absolute or relative path.
            Является ли ссылка абсолютной ОС, абсолютной от корня репозитория
            или относительной.
        format: Whether the link was written as markdown or wiki link.
            Была ли ссылка записана как markdown- или wiki-ссылка.
        start: Character offset where the link starts in the source content.
            Смещение символа, с которого ссылка начинается в исходном тексте.
        end: Character offset where the link ends in the source content.
            Смещение символа, на котором ссылка заканчивается в исходном тексте.
        header: The optional ``#fragment`` part of the link target.
            Опциональная часть фрагмента ``#fragment`` цели ссылки.
        is_image: ``True`` for image links (``![...](...)``).
            ``True`` для ссылок-изображений (``![...](...)``).
    """

    raw: str
    path: str
    text: str
    kind: LinkKind
    format: Literal["markdown", "wiki"]
    start: int
    end: int
    header: Optional[str] = None
    is_image: bool = False
