"""Check command CLI wiring.

Parses arguments, calls the check command, and prints the result.
No business logic lives here.

Разбор аргументов, вызов команды проверки и вывод результата.
Здесь нет бизнес-логики.
"""

import argparse
import logging
from typing import Optional

from ..command.check import run_check
from ..progress import progress_context
from ..validators import ValidationFailedError

from .formatters import print_skills, print_validation_report
from .source_parser import add_source_arguments, build_sources_from_args

# Module logger / Логгер модуля.
logger = logging.getLogger(__name__)


def add_parser(subparsers):
    """Register the ``check`` subcommand parser.

    Регистрирует парсер подкоманды ``check``.

    Args:
        subparsers: Argparse subparsers object. / Объект подпарсеров argparse.

    Returns:
        The configured parser. / Настроенный парсер.
    """
    parser = subparsers.add_parser(
        "check",
        help="Discover skills, validate them and print the result / "
             "Обнаружить навыки, проверить их и вывести результат",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_source_arguments(parser)
    parser.set_defaults(func=run)
    return parser


def run(args) -> int:
    """Execute the ``check`` command from parsed CLI arguments.

    Выполняет команду ``check`` из разобранных аргументов CLI.

    Args:
        args: Parsed argparse namespace. / Разобранное пространство имён argparse.

    Returns:
        Exit code. / Код завершения.
    """
    try:
        sources, _ = build_sources_from_args(args)

        with progress_context() as progress:
            skills, report = run_check(sources, progress=progress)

        print_skills(skills)
        if report.has_errors:
            print()
            print_validation_report(report)
            logger.error("Validation errors: %s", report)
            return 1

        print("\n✅ Validation passed")
        return 0
    except FileNotFoundError as e:
        logger.error("%s", e)
        return 1
    except ValueError as e:
        logger.error("%s", e)
        return 1
    except ValidationFailedError as e:
        if e.skills:
            print_skills(e.skills)
            print()
        print_validation_report(e.report)
        logger.error("Validation errors: %s", e)
        return 1
    except Exception as e:
        logger.error("Error: %s", e)
        return 1
