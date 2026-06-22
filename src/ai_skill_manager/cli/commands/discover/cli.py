"""Discover command CLI.

Parses arguments, calls the discovery API, and prints formatted output.
Разбирает аргументы, вызывает API обнаружения и печатает отформатированный вывод.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List

from ....config import build_sources_from_config
from ....entities import GitHubSource, LocalSource, Source
from ....services.discover import STRATEGIES, discover
from ....entities.skill import Skill
from .formatter import format_skills

DEFAULT_CONFIG = "ai-skills.yaml"
#: Default config file name. / Имя файла конфигурации по умолчанию.

DEFAULT_TARGET = ".agents/skills"
#: Default target directory (kept for CLI help compatibility).
#: Целевая директория по умолчанию (оставлена для совместимости справки CLI).


def add_parser(subparsers):
    """Register the ``discover`` subcommand parser.

    Регистрирует парсер подкоманды ``discover``.

    Args:
        subparsers: Argparse subparsers object. / Объект подпарсеров argparse.

    Returns:
        The configured parser. / Настроенный парсер.
    """
    parser = subparsers.add_parser(
        "discover",
        help="Discover skills and print them / Обнаружить навыки и вывести их",
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
        choices=list(STRATEGIES.keys()),
        help="Discovery strategy for a single source / "
             "Стратегия обнаружения для одного источника",
    )
    parser.add_argument(
        "-p",
        "--path",
        help="Source path or GitHub repo URL / Путь к источнику или URL репозитория GitHub",
    )
    parser.add_argument(
        "--tree",
        default="master",
        help="Git tree/branch when type=github (default: master) / "
             "Ветка/дерево Git при type=github (по умолчанию: master)",
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


def _discover(args) -> List[Skill]:
    """Resolve CLI arguments to a list of skills.

    Преобразует аргументы CLI в список навыков.

    Args:
        args: Parsed argparse namespace. / Разобранное пространство имён argparse.

    Returns:
        Discovered skills. / Обнаруженные навыки.

    Raises:
        FileNotFoundError: If the specified config file does not exist.
            / Если указанный файл конфигурации не существует.
        ValueError: If neither config nor source type is provided.
            / Если не указан ни конфиг, ни тип источника.
    """
    if args.config:
        # Explicit config file mode.
        # Режим с явно указанным файлом конфигурации.
        config_path = Path(args.config).resolve()
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")
        return discover(build_sources_from_config(config_path))

    if args.type:
        # Single source mode: type + path.
        # Режим одного источника: тип + путь.
        if not args.path:
            raise ValueError("--path is required when using --type")

        # GitHub sources default to the "skills" subpath unless overridden.
        # Для источников GitHub по умолчанию используется подпуть "skills", если не переопределён.
        subpath = args.subpath
        if args.type == "github" and subpath is None:
            subpath = "skills"

        # Build the appropriate source object based on the selected type.
        # Формируем соответствующий объект источника в зависимости от выбранного типа.
        if args.type == "github":
            source: Source = GitHubSource(
                repo_url=args.path,
                tree=args.tree,
                subpath=subpath,
            )
        else:
            source = LocalSource(path=Path(args.path))

        return discover([source])

    # Default: try ai-skills.yaml in the current directory.
    # По умолчанию: пробуем ai-skills.yaml в текущей директории.
    config_path = Path(DEFAULT_CONFIG).resolve()
    if config_path.exists():
        return discover(build_sources_from_config(config_path))

    raise ValueError(
        "No config file specified and no source type provided.\n"
        "   Use --config <file> or --type <auto|directory|flat|github> --path <source>"
    )


def run(args):
    """Execute the ``discover`` command from parsed CLI arguments.

    Выполняет команду ``discover`` из разобранных аргументов CLI.

    Args:
        args: Parsed argparse namespace. / Разобранное пространство имён argparse.
    """
    if args.verbose:
        # Enable debug logging for discovery strategies.
        # Включаем подробное логирование для стратегий обнаружения.
        logging.basicConfig(level=logging.DEBUG, format="%(message)s")

    try:
        skills = _discover(args)
        print(format_skills(skills))
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
