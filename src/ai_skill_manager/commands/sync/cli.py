"""Sync command CLI.

Parses arguments, calls the sync API, and prints the formatted result.
Разбирает аргументы, вызывает API синхронизации и печатает отформатированный результат.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from .api import DEFAULT_CONFIG, run_sync
from .formatter import format_sync_result


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
        default=DEFAULT_CONFIG,
        help=f"Config file (default: {DEFAULT_CONFIG}) / "
             f"Файл конфигурации (по умолчанию: {DEFAULT_CONFIG})",
    )
    parser.add_argument(
        "--target",
        help="Override target directory / Переопределить целевую директорию",
    )
    parser.add_argument(
        "--on-conflict",
        choices=["error", "last_wins"],
        help="Conflict resolution / Разрешение конфликтов",
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

    # Resolve the configuration file path to an absolute path.
    # Разрешаем путь к файлу конфигурации в абсолютный.
    config_path = Path(args.config).resolve()

    # Resolve conflicting orphan flags into a single boolean.
    # Преобразуем конфликтующие флаги orphan в одно булево значение.
    remove: Optional[bool] = None
    if args.remove_orphans:
        remove = True
    elif args.keep_orphans:
        remove = False

    try:
        result = run_sync(
            config_path=config_path,
            target_dir=Path(args.target) if args.target else None,
            on_conflict=args.on_conflict or "error",
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
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
