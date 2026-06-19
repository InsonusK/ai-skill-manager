"""Discover command output formatter.

Converts a list of ``Skill`` objects into a human-readable numbered list
for console output.

Преобразует список объектов ``Skill`` в читаемый нумерованный список
для вывода в консоль.
"""

from typing import List

from ...models.skill import Skill


def format_skills(skills: List[Skill]) -> str:
    """Format a list of Skill objects as a numbered string.

    Args:
        skills: Discovered skills. / Обнаруженные навыки.

    Returns:
        Numbered multi-line string or a "no skills" message.
        / Нумерованная многострочная строка или сообщение об отсутствии навыков.

    Example:
        >>> format_skills([Skill(file_path=Path("guide.skill.md"), folder_path=None)])
        '1. guide | flat | guide.skill.md\n    File: ...'
    """
    if not skills:
        return "No skills discovered."

    lines = []
    for i, skill in enumerate(skills, start=1):
        name = skill.name or "(unnamed)"
        kind = "flat" if skill.is_flat() else "directory"
        lines.append(f"{i}. {name} | {kind} | {skill.file_path.name}")
        lines.append(f"    File: {skill.file_path}")

    lines.append(f"\nTotal: {len(skills)} skill(s)")
    return "\n".join(lines)
