"""Discover command CLI.

Parses arguments, calls the discovery API, and prints formatted output.
Разбирает аргументы, вызывает API обнаружения и печатает отформатированный вывод.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List

from ...config import load_config
from .core.base import SkillMapping
from .api import (
    DEFAULT_CONFIG,
    DEFAULT_TARGET,
    discover_from_config,
    discover_single_source,
    resolve_target,
    STRATEGIES
)
from .formatter import format_mappings


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
        help="Discover skills and print mappings / Обнаружить навыки и вывести сопоставления",
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
        "--target",
        help=f"Override target directory (default: {DEFAULT_TARGET}) / "
             f"Переопределить целевую директорию (по умолчанию: {DEFAULT_TARGET})",
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
    parser.set_defaults(func=run)
    return parser


def _discover(args) -> List[SkillMapping]:
    """Resolve CLI arguments to a list of skill mappings.

    Преобразует аргументы CLI в список сопоставлений навыков.

    Args:
        args: Parsed argparse namespace. / Разобранное пространство имён argparse.

    Returns:
        Discovered skill mappings. / Обнаруженные сопоставления навыков.

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
        target_dir = resolve_target(
            config_path.parent,
            load_config(config_path).get("settings", {}),
            args.target,
        )
        return discover_from_config(config_path, target_dir)

    if args.type:
        # Single source mode: type + path.
        # Режим одного источника: тип + путь.
        target_dir = (
            Path(args.target).resolve()
            if args.target
            else Path(DEFAULT_TARGET).resolve()
        )
        return discover_single_source(
            args.type,
            args.path,
            target_dir,
            tree=args.tree,
            subpath=args.subpath,
        )

    # Default: try ai-skills.yaml in the current directory.
    # По умолчанию: пробуем ai-skills.yaml в текущей директории.
    config_path = Path(DEFAULT_CONFIG).resolve()
    if config_path.exists():
        target_dir = resolve_target(
            config_path.parent,
            load_config(config_path).get("settings", {}),
            args.target,
        )
        return discover_from_config(config_path, target_dir)

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
        mappings = _discover(args)
        print(format_mappings(mappings))
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
