"""One link's resolution failure: the raw link text plus why it failed.

Ошибка резолюции одной ссылки: сырой текст ссылки и причина сбоя.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LinkError:
    """A single link's raw text paired with the reason it could not be resolved.

    Сырой текст одной ссылки вместе с причиной, по которой её не удалось разрешить.
    """

    raw: str
    """The link exactly as written in the source file (e.g. ``[b](../b/SKILL.md)``).
    Ссылка в точности как она написана в исходном файле."""

    message: str
    """Why resolution failed, without repeating the raw link text.
    Причина сбоя резолюции, без повторения сырого текста ссылки."""
