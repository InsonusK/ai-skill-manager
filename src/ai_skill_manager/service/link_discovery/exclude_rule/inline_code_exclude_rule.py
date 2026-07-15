"""Exclude rule for links inside inline code spans.

Правило исключения ссылок, находящихся внутри инлайн-кода.
"""

import re
from pathlib import Path
from typing import Dict, Match

from ....models import LinkWithContext
from .abs_exclude_rule import absExcludeRule


class InlineCodeExcludeRule(absExcludeRule):
    """Skip links wrapped in single backtick inline code spans.

    Fenced code blocks are masked before detection so that links inside plain
    `` ``` `` blocks are still validated.

    Пропускает ссылки, обёрнутые в инлайн-код из одной обратной кавычки.
    Fenced code blocks маскируются перед проверкой, чтобы ссылки внутри
    обычных `` ``` `` блоков всё ещё валидировались.
    """

    def __init__(self) -> None:
        """Initialize the rule with an empty mask cache."""
        self.__masked_cache: Dict[Path, str] = {}

    def should_exclude(self, link: LinkWithContext) -> bool:
        """Return ``True`` if the link lies inside inline code."""
        file_path = link.file_path
        masked = self.__masked_cache.get(file_path)
        if masked is None:
            masked = _mask_fenced_blocks_for_inline_code(link.content)
            self.__masked_cache[file_path] = masked
        return _is_inside_inline_code(masked, link.base.start, link.base.end)


# Matches fenced code blocks (3+ backticks, optional language label). Used to
# exclude such blocks when looking for inline code spans so that links inside
# plain ``` blocks are still validated.
# Совпадает с fenced code blocks (3+ обратных кавычки, необязательная метка
# языка). Используется для исключения таких блоков при поиске инлайн-кода,
# чтобы ссылки внутри обычных ``` блоков всё ещё проверялись.
_FENCED_BLOCK_RE = re.compile(
    r"^[ ]{0,3}(`{3,})[^\n]*$\n?.*?^[ ]{0,3}\1\s*$",
    re.MULTILINE | re.DOTALL,
)


def _mask_fenced_blocks_for_inline_code(content: str) -> str:
    """Replace fenced code blocks with spaces.

    The returned string has the same length as ``content`` so that link offsets
    stay valid for the original document.

    Возвращает строку той же длины, что и ``content``, чтобы смещения ссылок
    оставались корректными для оригинального документа.
    """

    def _replace_with_spaces(match: Match[str]) -> str:
        return " " * len(match.group(0))

    return _FENCED_BLOCK_RE.sub(_replace_with_spaces, content)


def _is_inside_inline_code(masked_content: str, start: int, end: int) -> bool:
    """Return ``True`` if the span ``[start, end]`` lies inside inline code.

    Only single backtick inline code spans (`` `...` ``) are considered.
    The content must already have fenced code blocks masked.

    Возвращает ``True``, если диапазон ``[start, end]`` находится внутри
    инлайн-кода. Учитываются только пары из одной обратной кавычки.
    Содержимое должно быть уже очищено от fenced code blocks.
    """
    backtick_re = re.compile(r"`+")
    pos = 0
    while True:
        match = backtick_re.search(masked_content, pos)
        if not match:
            break
        open_start = match.start()
        open_len = len(match.group(0))
        closing_re = re.compile(rf"`{{{open_len}}}(?!`)")
        closing_match = closing_re.search(masked_content, match.end())
        if not closing_match:
            break
        close_start = closing_match.start()
        close_end = closing_match.end()
        if start < close_end and end > open_start:
            return True
        pos = close_end
    return False
