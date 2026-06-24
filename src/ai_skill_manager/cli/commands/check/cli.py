"""Check command CLI.

Discovers skills, validates them, and prints the result.
Обнаруживает навыки, проверяет их и выводит результат.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List

from ...tools.source_parser import build_sources_from_args
from ...tools.validation_report_printer import print_validation_report

from ....entities.skill import Skill
from ....services.discover import discover
from ....services.validate import validate
from ....validators import ValidationFailedError
from .formatter import format_skills

DEFAULT_CONFIG = "ai-skills.yaml"
#: Default config file name. / Имя файла конфигурации по умолчанию.

# Source types supported by the check CLI. / Типы источников, поддерживаемые CLI check.
_CHECK_TYPES = ["auto", "github"]


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
    parser.add_argument(
        "-c",
        "--config",
        default=None,
        help=f"Config file (default: {DEFAULT_CONFIG}) / "
             f"Файл конфигурации (по умолчанию: {DEFAULT_CONFIG})",
    )
    parser.add_argument(
        "-t",
        "--type",
        choices=_CHECK_TYPES,
        help="Discovery strategy for a single source / "
             "Стратегия обнаружения для одного источника",
    )
    parser.add_argument(
        "-p",
        "--path",
        help="Source path or GitHub repo URL (with optional branch: 'url branch') / "
             "Путь к источнику или URL репозитория GitHub (с опциональной веткой: 'url branch')",
    )
    parser.add_argument(
        "--subpath",
        action="append",
        default=None,
        help="GitHub subpath when type=github (can be repeated; default: skills) / "
             "Подпуть в GitHub при type=github (можно повторять; по умолчанию: skills)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging / Включить подробное логирование",
    )
    # Wire the default command function for this subparser.
    # Связываем функцию команды по умолчанию для этого подпарсера.
    parser.set_defaults(func=run)
    return parser


def _check(args) -> List[Skill]:
    """Resolve CLI arguments to a list of skills.

    Преобразует аргументы CLI в список навыков.

    Args:
        args: Parsed argparse namespace. / Разобранное пространство имён argparse.

    Returns:
        Discovered skills. / Обнаруженные навыки.
    """
    sources, _ = build_sources_from_args(args)
    return discover(sources)


def run(args):
    """Execute the ``check`` command from parsed CLI arguments.

    Выполняет команду ``check`` из разобранных аргументов CLI.

    Args:
        args: Parsed argparse namespace. / Разобранное пространство имён argparse.
    """
    if args.verbose:
        # Enable debug logging for discovery strategies.
        # Включаем подробное логирование для стратегий обнаружения.
        logging.basicConfig(level=logging.DEBUG, format="%(message)s")

    try:
        skills = _check(args)
        report = validate(skills)

        if report.has_errors:
            print(format_skills(skills))
            print()
            print_validation_report(report)
            raise ValidationFailedError(report)

        print(format_skills(skills))
        print("\n✅ Validation passed")
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    except ValidationFailedError as e:
        print(f"❌ Validation Errors: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
