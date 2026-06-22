from typing import List

from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from ...validators.models import ValidationReport


def print_validation_report(report: ValidationReport):
    console = Console()
    tree = Tree("[bold red]Validation Failed[/bold red]")

    for skill, rule_errors in report.result.items():
        skill_branch = tree.add(f"[cyan]{skill}[/cyan]")
        for rule, result in rule_errors.items():
            rule_branch = skill_branch.add(f"[green]{rule}[/green]")
            for error in result.errors:
                rule_branch.add(f"[red]• {error}[/red]")
    console.print(tree)
    console.print(
        f"\nTotal: {sum(len(r.errors) for s in report.result.values() for r in s.values())} error(s)")
