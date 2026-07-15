"""CLI output formatters.

Converts command results into human-readable terminal output. Rich console
rendering stays in the CLI layer.

Форматёры вывода CLI.
Преобразуют результаты команд в читаемый терминальный вывод. Рендеринг
через Rich остаётся в слое CLI.
"""

from typing import Any, Dict, List

from rich.console import Console
from rich.text import Text
from rich.tree import Tree

from ...entities.skill_v2 import Skill
from ...sync_exception import SyncFailedError


def format_sync_result(result: Dict[str, Any]) -> str:
    """Format sync result dictionary as console output.

    Форматирует словарь результата синхронизации для вывода в консоль.

    Args:
        result: Dictionary returned by ``run_sync``. / Словарь, возвращённый ``run_sync``.

    Returns:
        Multi-line formatted string. / Многострочная отформатированная строка.
    """
    lines = []

    synced_count = result.get("skills_count", 0)
    lines.append(f"\n📊 Synced: {synced_count} skills")

    if result.get("dry_run"):
        lines.append("\n🏃 Dry run - no changes")

    return "\n".join(lines)


def format_skills(skills: List[Skill]) -> str:
    """Format a list of Skill objects as a plain string.

    Returns a plain string representation. When no skills are discovered a
    simple message is returned.

    Args:
        skills: Discovered skills. / Обнаруженные навыки.

    Returns:
        Formatted string. / Отформатированная строка.
    """
    if not skills:
        return "No skills discovered."

    lines = ["Discovered skills"]
    for skill in sorted(skills, key=lambda s: s.name):
        lines.append(f"  {skill.name}")
        for skill_file in skill.files:
            lines.append(f"    {skill_file.path}")

    lines.append(f"\nTotal: {len(skills)} skill(s)")
    return "\n".join(lines)


def print_skills(skills: List[Skill]) -> None:
    """Print a list of Skill objects as a rich tree.

    Args:
        skills: Discovered skills. / Обнаруженные навыки.
    """
    if not skills:
        print("No skills discovered.")
        return

    console = Console()
    tree = Tree("[bold]Discovered skills[/bold]")

    for skill in sorted(skills, key=lambda s: s.name):
        skill_branch = tree.add(f"[cyan]{skill.name}[/cyan]")
        for skill_file in skill.files:
            skill_branch.add(str(skill_file.path))

    console.print(tree)
    console.print(f"\nTotal: {len(skills)} skill(s)")


def print_sync_errors(error: SyncFailedError) -> None:
    """Print the errors collected during a failed sync run.

    Печатает ошибки, собранные во время неудачного запуска синхронизации.

    Args:
        error: The raised sync failure, carrying the collected errors and
            the untouched target path.
            / Возникшая ошибка синхронизации, содержащая собранные ошибки и
            нетронутый путь target.
    """
    console = Console()
    tree = Tree(f"[bold red]Sync Failed[/bold red] ({len(error.errors)} error(s))")
    for message in error.errors:
        tree.add(Text(message, style="red"))

    console.print(tree)
    console.print(f"\n[bold]{error.target_dir}[/bold] was left unchanged.")
