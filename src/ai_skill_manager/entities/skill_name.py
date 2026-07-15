"""Skill name format validation.

Валидация формата имени скилла.
"""

import re

_KEBAB_CASE_RE = re.compile(r"^[a-z0-9]+(-{1,2}[a-z0-9]+)*$")


def is_kebab_case(name: str) -> bool:
    """Return ``True`` if ``name`` is lower-kebab-case.

    Allows single and double dashes as separators (``my-skill``,
    ``my--skill``) but not three or more in a row, and never at the edges.

    Возвращает ``True``, если ``name`` в нижнем kebab-case. Допускает
    одинарные и двойные дефисы как разделители (``my-skill``,
    ``my--skill``), но не три и более подряд, и никогда по краям.
    """
    if not name:
        return False
    return bool(_KEBAB_CASE_RE.match(name))
