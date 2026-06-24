"""Sync command CLI.

Parses arguments, calls the sync API, and prints the formatted result.
Разбирает аргументы, вызывает API синхронизации и печатает отформатированный результат.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from ...tools.source_parser import build_sources_from_args
from ...tools.validation_report_printer import print_validation_report

from ....validators import ValidationFailedError

from .api import DEFAULT_CONFIG, run_sync
from .formatter import format_sync_result


# Source types exposed by the sync CLI. / Типы источников, доступные в CLI sync.
_SYNC_TYPES = ["auto", "github"]


def add_parser(subparsers):
    """Register the ``sync`` subcommand parser.

    Регистрирует парсер подкоманды ``sync``.

    Args:
        subparsers: Argparse subparsers object. / Объект подпарсеров argparse.

    Returns:
        The configured parser. / Настроенный парсер.
    """
    parser = subparsers.add_parser(
        "sync",
        help="Sync AI skills into .agents/skills/ / "
             "Синхронизировать AI-навыки в .agents/skills/",
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
        choices=_SYNC_TYPES,
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
        "--target",
        help="Override target directory / Переопределить целевую директорию",
    )
    parser.add_argument(
        "--remove-orphans",
        action="store_true",
        default=None,
        help="Remove orphan skills / Удалить осиротевшие навыки",
    )
    parser.add_argument(
        "--keep-orphans",
        action="store_true",
        help="Keep orphan skills / Оставить осиротевшие навыки",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes / Показать изменения без записи",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force copy all skills, skip hash and version checks / "
             "Принудительно скопировать все навыки, пропустив проверку хеша и версии",
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


logger = logging.Logger("sync cli")


def run(args):
    """Execute the ``sync`` command from parsed CLI arguments.

    Выполняет команду ``sync`` из разобранных аргументов CLI.

    Args:
        args: Parsed argparse namespace. / Разобранное пространство имён argparse.
    """
    if args.verbose:
        # Enable debug logging across the synchronization pipeline.
        # Включаем подробное логирование во всём конвейере синхронизации.
        logging.basicConfig(level=logging.DEBUG, format="%(message)s")

    # Resolve conflicting orphan flags into a single boolean.
    # Преобразуем конфликтующие флаги orphan в одно булево значение.
    remove: Optional[bool] = None
    if args.remove_orphans:
        remove = True
    elif args.keep_orphans:
        remove = False

    try:
        # Resolve sources from --config, --type/--path or the default config.
        # Разрешаем источники из --config, --type/--path или конфигурации по умолчанию.
        sources, config_path = build_sources_from_args(args)
        if config_path is not None:
            result = run_sync(
                config_path=config_path,
                target_dir=Path(args.target) if args.target else None,
                remove_orphans=remove if remove is not None else True,
                dry_run=args.dry_run,
                force=args.force,
            )
        else:
            result = run_sync(
                sources=sources,
                target_dir=Path(args.target) if args.target else None,
                remove_orphans=remove if remove is not None else True,
                dry_run=args.dry_run,
                force=args.force,
            )
        print(format_sync_result(result))
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    except ValidationFailedError as e:
        print_validation_report(e.report)
        print(f"❌ Validation Errors: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
