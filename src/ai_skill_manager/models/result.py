"""Generic wrapper for a value paired with collected non-fatal errors.

Общая обёртка для значения вместе с собранными нефатальными ошибками.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Iterator, List, Tuple, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Result(Generic[T]):
    """A value together with any per-candidate errors collected while building it.

    Replaces the ad-hoc ``Tuple[T, List[str]]`` return shape used across
    discovery/enrichment steps so a bare ``List[str]`` in a signature isn't
    ambiguous - it is always errors, never the primary result.

    Значение вместе с любыми ошибками по отдельным кандидатам, собранными
    при его построении. Заменяет разрозненную форму возврата
    ``Tuple[T, List[str]]``, использовавшуюся в шагах обнаружения/обогащения,
    чтобы голый ``List[str]`` в сигнатуре не был неоднозначным - это всегда
    ошибки, а не основной результат.

    Supports tuple-style unpacking (``value, errors = result``) so existing
    call sites do not need to switch to attribute access.

    Поддерживает распаковку в стиле кортежа (``value, errors = result``),
    поэтому существующим местам вызова не нужно переходить на доступ через
    атрибуты.
    """

    value: T
    errors: List[str]

    @property
    def has_errors(self) -> bool:
        """Return whether any errors were collected."""
        return bool(self.errors)

    def __iter__(self) -> Iterator:
        """Yield ``(value, errors)`` so ``a, b = result`` keeps working."""
        return iter((self.value, self.errors))

    def as_tuple(self) -> Tuple[T, List[str]]:
        """Return the ``(value, errors)`` pair explicitly."""
        return self.value, self.errors
