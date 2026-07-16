"""Raw link data produced by syntax parsing, before classification.

Сырые данные ссылки, полученные синтаксическим разбором, до классификации.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LinkData:
    """A single link exactly as found by syntax parsing.

    Holds only what pure syntax scanning can know about a link: the raw
    source text, display text, link format identifier, offsets, optional
    ``#fragment``, image flag, and the raw (unclassified) path or URL
    exactly as written. Deciding whether that raw value is a web address or
    a file reference - and resolving a file reference's target - is not this
    class's concern; that happens later, in ``service.link_discovery``,
    producing an :class:`~ai_skill_manager.entities.link.abs_link.absLink`
    subclass (:class:`FileLink` or :class:`WebLink`).

    Одна ссылка в точности так, как она найдена синтаксическим разбором.
    Содержит только то, что может знать чистое сканирование синтаксиса:
    исходный текст, отображаемый текст, идентификатор формата ссылки,
    смещения, опциональный ``#fragment``, флаг изображения и сырой
    (неклассифицированный) путь или URL в точности как он написан. Решение о
    том, является ли это сырое значение веб-адресом или файловой ссылкой - и
    резолюция цели файловой ссылки - не забота этого класса; это происходит
    позже, в ``service.link_discovery``, порождая подкласс
    :class:`~ai_skill_manager.entities.link.abs_link.absLink`
    (:class:`FileLink` или :class:`WebLink`).

    Attributes:
        raw: The exact link text as it appears in the source.
            Точный текст ссылки в исходнике.
        text: The display text of the link.
            Отображаемый текст ссылки.
        format: Identifier of the syntax that produced this link
            (e.g. ``"markdown"`` or ``"wikilink"``).
            Идентификатор синтаксиса, породившего эту ссылку
            (например, ``"markdown"`` или ``"wikilink"``).
        start: Character offset where the link starts in the source content.
            Смещение символа, с которого ссылка начинается в исходном тексте.
        end: Character offset where the link ends in the source content.
            Смещение символа, на котором ссылка заканчивается в исходном тексте.
        raw_path: The link target exactly as written, not yet classified as
            a web address or a file reference.
            Цель ссылки в точности как она написана, ещё не классифицированная
            как веб-адрес или файловая ссылка.
        header: The optional ``#fragment`` part of the link target.
            Опциональная часть фрагмента ``#fragment`` цели ссылки.
        is_image: ``True`` for image links (``![...](...)``).
            ``True`` для ссылок-изображений (``![...](...)``).
    """

    raw: str
    text: str
    format: str
    start: int
    end: int
    raw_path: str
    header: Optional[str]
    is_image: bool
