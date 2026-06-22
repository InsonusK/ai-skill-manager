from typing import Dict
from ...validators.rules import absValidationRule
from ...entities import Skill,Source
from rich.console import Console
from rich.tree import Tree
from ...validators.models import ValidationReport,ValidationResult


def print_validation_report(report: ValidationReport):
    console = Console()
    tree = Tree("[bold red]Validation Failed[/bold red]")
    source_reports:Dict[Source,Dict[Skill, Dict[absValidationRule, ValidationResult]]] = { }
    for skill, rule_errors in report.result.items():
        source_report:Dict[Skill, Dict[absValidationRule, ValidationResult]] = source_reports.get(skill.source, {})
        source_report[skill] = rule_errors
        source_reports[skill.source] = source_report
    
    for source, source_report in source_reports.items():
        source_branch = tree.add(f"[cyan]{source}")
        for skill, rule_errors in report.result.items():
            skill_branch = source_branch.add(f"{skill.name}\n{skill.file_path}")
            for rule, result in rule_errors.items():
                rule_branch = skill_branch.add(f"[green]{rule.name} {rule.version}[/green]: {len(result.errors)} errors(s)")
                for error in result.errors:
                    rule_branch.add(f"[red]{error}[/red]")
    console.print(tree)
    console.print(
        f"\nTotal: {sum(len(r.errors) for s in report.result.values() for r in s.values())} error(s)")
