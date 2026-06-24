"""Discover command output printer.

Prints a list of ``Skill`` objects as a human-readable tree grouped by
source, skill and files for console output.

Выводит список объектов ``Skill`` в виде читаемого дерева,
сгруппированного по источнику, навыку и файлам.
"""

from typing import Dict, List

from rich.console import Console
from rich.tree import Tree

from ....entities.skill import Skill
from ....entities.source import Source


def print_skills(skills: List[Skill]) -> None:
    """Print a list of Skill objects as a tree grouped by source.

    Args:
        skills: Discovered skills. / Обнаруженные навыки.
    """
    if not skills:
        print("No skills discovered.")
        return

    console = Console()
    tree = Tree("[bold]Discovered skills[/bold]")

    source_reports: Dict[Source, List[Skill]] = {}
    for skill in skills:
        source_report = source_reports.get(skill.source, [])
        source_report.append(skill)
        source_reports[skill.source] = source_report

    for source, source_skills in source_reports.items():
        source_branch = tree.add(f"[cyan]{source}[/cyan]")
        for skill in source_skills:
            name = skill.name or "(unnamed)"
            skill_branch = source_branch.add(f"{name}")
            for skill_file in skill.files:
                rel_path = skill_file.path.relative_to(skill.source_path)
                skill_branch.add(str(rel_path))

    console.print(tree)
    console.print(f"\nTotal: {len(skills)} skill(s)")
