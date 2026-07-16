"""Exclude rule for links inside ```example fenced code blocks.

Правило исключения ссылок внутри fenced code block ```example.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple

from ....models import LinkWithContext
from .abs_exclude_rule import absExcludeRule

# Matches fenced code blocks labelled ``example`` (optionally indented by up to
# three spaces, per CommonMark). Documentation uses such blocks to show link
# syntax without those links being treated as real, resolvable links.
# Совпадает с fenced code blocks, помеченными ``example`` (с отступом до трёх
# пробелов, как в CommonMark). Документация использует такие блоки, чтобы
# показать синтаксис ссылок без того, чтобы эти ссылки считались настоящими,
# разрешаемыми ссылками.
_EXAMPLE_BLOCK_RE = re.compile(
    r"^[ ]{0,3}```example\s*$\n?.*?^[ ]{0,3}(?:```\s*$|\Z)",
    re.MULTILINE | re.DOTALL,
)


class ExampleBlockExcludeRule(absExcludeRule):
    """Skip links found inside ```example fenced code blocks.

    Пропускает ссылки, находящиеся внутри fenced code block ```example.
    """

    def __init__(self) -> None:
        """Initialize the rule with an empty block-span cache."""
        self.__spans_cache: Dict[Path, List[Tuple[int, int]]] = {}

    def should_exclude(self, link: LinkWithContext) -> bool:
        """Return ``True`` if the link lies inside a ```example block."""
        file_path = link.file_path
        spans = self.__spans_cache.get(file_path)
        if spans is None:
            spans = [match.span() for match in _EXAMPLE_BLOCK_RE.finditer(link.content)]
            self.__spans_cache[file_path] = spans
        start, end = link.base.start, link.base.end
        return any(block_start <= start and end <= block_end for block_start, block_end in spans)
