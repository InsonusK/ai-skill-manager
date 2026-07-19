"""CLI output formatters.

Converts command results into human-readable terminal output. Rich console
rendering stays in the CLI layer.

Форматёры вывода CLI.
Преобразуют результаты команд в читаемый терминальный вывод. Рендеринг
через Rich остаётся в слое CLI.
"""

from pathlib import Path
from typing import Any, Dict, List, Tuple

from rich.console import Console
from rich.text import Text
from rich.tree import Tree

from ...entities.skill_v2 import Skill
from ...models.link_validation_error import LinkValidationError
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


def build_sync_errors_tree(error: SyncFailedError) -> Tree:
    """Build the ``rich.tree.Tree`` reporting a failed sync run's errors.

    Строит ``rich.tree.Tree`` для отчёта об ошибках неудачного запуска синхронизации.

    Plain string errors (e.g. duplicate skill names) are added as flat leaves
    under the root. ``LinkValidationError`` entries are grouped by
    ``(skill_name, skill_path)`` and then by ``file_relative_path``, so a
    skill/file with several broken links gets one ``Skill``/``File`` node
    with each link as its own child, instead of repeating the skill/file
    context per link:

        Skill {name}
        path: {skill_path}
          File {file_relative_path}
            Link {link_raw}
            error: {message}

    Разделены на группы по ``(skill_name, skill_path)``, а затем по
    ``file_relative_path``, так что скилл/файл с несколькими битыми ссылками
    получает один узел ``Skill``/``File``, где каждая ссылка - свой дочерний
    узел, вместо повторения контекста скилла/файла для каждой ссылки.
    """
    tree = Tree(f"[bold red]Sync Failed[/bold red] ({len(error.errors)} error(s))")

    skill_groups: Dict[Tuple[str, Path], Dict[Path, List[LinkValidationError]]] = {}

    for err in error.errors:
        if isinstance(err, LinkValidationError):
            file_groups = skill_groups.setdefault((err.skill_name, err.skill_path), {})
            file_groups.setdefault(err.file_relative_path, []).append(err)
        else:
            tree.add(Text(err, style="red"))

    for (skill_name, skill_path), file_groups in skill_groups.items():
        skill_node = tree.add(Text(f"Skill {skill_name}\npath: {skill_path}", style="red"))
        for file_relative_path, link_errors in file_groups.items():
            file_node = skill_node.add(Text(f"File {file_relative_path}", style="red"))
            for link_error in link_errors:
                file_node.add(Text(f"Link {link_error.link_raw}\nerror: {link_error.message}", style="red"))

    return tree


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
    console.print(build_sync_errors_tree(error))
    console.print(f"\n[bold]{error.target_dir}[/bold] was left unchanged.")
