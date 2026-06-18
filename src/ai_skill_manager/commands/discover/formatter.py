"""Discover command output formatter.

Converts a list of ``SkillMapping`` objects into a human-readable numbered
list for console output.

Преобразует список объектов ``SkillMapping`` в читаемый нумерованный список
для вывода в консоль.
"""

from typing import List

from .models.skill_mapping import SkillMapping


def format_mappings(mappings: List[SkillMapping]) -> str:
    """Format a list of SkillMapping as a numbered string.

    Форматирует список SkillMapping в виде нумерованной строки.

    Args:
        mappings: Discovered skill mappings. / Обнаруженные сопоставления навыков.

    Returns:
        Numbered multi-line string or a "no skills" message.
        / Нумерованная многострочная строка или сообщение об отсутствии навыков.

    Example:
        >>> format_mappings([SkillMapping(..., skill_name="guide", is_flat=True)])
        '1. guide | flat | guide.skill.md\n    Source: ...\n    Target: ...\n\nTotal: 1 skill(s)'
    """
    if not mappings:
        return "No skills discovered."

    lines = []
    for i, m in enumerate(mappings, start=1):
        skill_md = m.source_skill_md.name if m.source_skill_md else ""
        lines.append(
            f"{i}. {m.skill_name} | "
            f"{'flat' if m.is_flat else 'directory'} | {skill_md}"
        )
        lines.append(f"    Source: {m.source_path}")
        lines.append(f"    Target: {m.target_path}")

    lines.append(f"\nTotal: {len(mappings)} skill(s)")
    return "\n".join(lines)
