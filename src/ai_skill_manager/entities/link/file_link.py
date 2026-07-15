"""FileLink entity: one parsed link occurrence and its resolved target.

Сущность FileLink: одно распарсенное вхождение ссылки и её разрешённая цель.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Type

if TYPE_CHECKING:
    from ...discovery.link.builder.abs_link_builder import absLinkBuilder
    from .link_target import LinkTarget


@dataclass(eq=True)
class FileLink:
    """A single link found in a file, with its resolved target.

    Одна ссылка, найденная в файле, с её разрешённой целью.
    """

    raw: str
    """Exact link text as it appears in the source.
    Точный текст ссылки в исходнике."""

    text: str
    """Display text of the link. / Отображаемый текст ссылки."""

    format: Type["absLinkBuilder"]
    """Builder that produced this link (markdown or wiki syntax).
    Сборщик, создавший эту ссылку (markdown или wiki синтаксис)."""

    start: int
    """Character offset where the link starts. / Смещение начала ссылки."""

    end: int
    """Character offset where the link ends. / Смещение конца ссылки."""

    target: "LinkTarget"
    """Resolved target this link points to. / Разрешённая цель, на которую указывает ссылка."""

    header: Optional[str] = None
    """Optional ``#fragment`` when the link points at a markdown subsection.
    Опциональный ``#fragment``, если ссылка указывает на подраздел markdown."""

    is_image: bool = False
    """``True`` for image links (``![...](...)``).
    ``True`` для ссылок-изображений (``![...](...)``)."""
