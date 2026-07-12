"""Sync command CLI wiring.

Parses arguments, calls the sync command, and prints the formatted result.
No business logic lives here.

Разбор аргументов, вызов команды синхронизации и вывод результата.
Здесь нет бизнес-логики.
"""

import argparse
import logging
from pathlib import Path
from typing import Optional

from ..command.sync import run_sync
from ..progress import progress_context
from ..sync_exception import SyncFailedError
from ..validators import ValidationFailedError

from .common.formatters import (
    format_sync_result,
    print_skills,
    print_sync_errors,
    print_validation_report,
)
from .common.source_parser import add_source_arguments, build_sources_from_args

# Module logger / Логгер модуля.
logger = logging.getLogger(__name__)


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
    add_source_arguments(parser)
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
    parser.set_defaults(func=run)
    return parser


def _resolve_remove_orphans(args) -> Optional[bool]:
    """Resolve conflicting orphan flags into a single boolean or None."""
    if args.remove_orphans:
        return True
    if args.keep_orphans:
        return False
    return None


def run(args) -> int:
    """Execute the ``sync`` command from parsed CLI arguments.

    Выполняет команду ``sync`` из разобранных аргументов CLI.

    Args:
        args: Parsed argparse namespace. / Разобранное пространство имён argparse.

    Returns:
        Exit code. / Код завершения.
    """
    remove = _resolve_remove_orphans(args)

    try:
        sources, config_path = build_sources_from_args(args)
        target_dir = Path(args.target) if args.target else None

        with progress_context() as progress:
            if config_path is not None:
                result = run_sync(
                    config_path=config_path,
                    target_dir=target_dir,
                    remove_orphans=remove,
                    dry_run=args.dry_run,
                    force=args.force,
                    progress=progress,
                )
            else:
                result = run_sync(
                    sources=sources,
                    target_dir=target_dir,
                    remove_orphans=remove,
                    dry_run=args.dry_run,
                    force=args.force,
                    progress=progress,
                )

        print_skills(result["skills"])
        print(format_sync_result(result))
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
    except SyncFailedError as e:
        print_sync_errors(e)
        logger.error("Sync errors: %s", e)
        return 1
    except Exception as e:
        logger.error("Error: %s", e)
        return 1

