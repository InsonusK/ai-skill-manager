"""Discover command output formatter."""

from typing import List

from ...discovery.base import SkillMapping


def format_mappings(mappings: List[SkillMapping]) -> str:
    """Format a list of SkillMapping as a numbered string."""
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
