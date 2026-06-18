"""New skill CLI.

Defines argument parsing and wires the API call to the formatter.
Определяет парсинг аргументов и связывает вызов API с форматёром.
"""

import argparse
import sys
from pathlib import Path

from .api import SkillExistsError, SkillType, create_skill
from .formatter import format_created


def add_parser(subparsers):
    """Register the ``new`` subcommand parser.

    Регистрирует парсер подкоманды ``new``.

    Args:
        subparsers: Argparse subparsers object. / Объект подпарсеров argparse.

    Returns:
        The configured parser. / Настроенный парсер.
    """
    parser = subparsers.add_parser(
        "new",
        help="Create a new skill",
    )
    parser.add_argument("skill_name", help="Name of the new skill / Имя нового навыка")
    parser.add_argument(
        "path",
        help="Path to the folder where the skill will be created / "
             "Путь к папке, где будет создан навык",
    )
    parser.add_argument(
        "--type",
        choices=["flat", "dir"],
        default="dir",
        help="Skill type: flat (single SKILL.md file) or dir (skill folder with SKILL.md inside) / "
             "Тип навыка: flat (один файл SKILL.md) или dir (папка навыка с SKILL.md внутри)",
    )
    parser.set_defaults(func=run)
    return parser


def run(args):
    """Execute the ``new`` command from parsed CLI arguments.

    Выполняет команду ``new`` из разобранных аргументов CLI.

    Args:
        args: Namespace with ``skill_name``, ``path`` and ``type``. /
            Пространство имён с ``skill_name``, ``path`` и ``type``.
    """
    try:
        # Call the pure API and format the returned Path.
        # Вызываем чистое API и форматируем возвращённый Path.
        created = create_skill(args.skill_name, Path(args.path), args.type)
        print(format_created(created, args.type == "flat"))
    except SkillExistsError as e:
        # Report file-system conflicts to stderr and exit with error code.
        # Сообщаем о конфликтах файловой системы в stderr и завершаем с кодом ошибки.
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
