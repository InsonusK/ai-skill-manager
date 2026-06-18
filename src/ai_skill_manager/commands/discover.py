"""Discover command.

Run skill discovery from a config file or a single source and print the
resulting SkillMapping list as a table.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

from ..config import load_config
from ..core import STRATEGIES
from ..discovery.base import SkillMapping
from ..discovery.github import GitHubDiscovery

DEFAULT_CONFIG = "ai-skills.yaml"
DEFAULT_TARGET = ".agents/skills"


def add_parser(subparsers):
    parser = subparsers.add_parser(
        'discover',
        help='Discover skills and print mappings',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '-c', '--config', default=None,
        help=f'Config file (default: {DEFAULT_CONFIG})',
    )
    parser.add_argument(
        '-t', '--type', choices=list(STRATEGIES.keys()),
        help='Discovery strategy for a single source',
    )
    parser.add_argument(
        '-p', '--path', help='Source path or GitHub repo URL',
    )
    parser.add_argument(
        '--target', help=f'Override target directory (default: {DEFAULT_TARGET})',
    )
    parser.add_argument(
        '--tree', default='master',
        help='Git tree/branch when type=github (default: master)',
    )
    parser.add_argument(
        '--subpath', action='append', default=None,
        help='GitHub subpath when type=github (can be repeated; default: skills)',
    )
    parser.add_argument(
        '-v', '--verbose', action='store_true',
        help='Enable debug logging',
    )
    parser.set_defaults(func=run)
    return parser


def _resolve_target(config_dir: Path, settings: dict, args_target: Optional[str]) -> Path:
    """Resolve target directory from args, config settings, or default."""
    if args_target:
        return Path(args_target).resolve()
    if 'target' in settings:
        return config_dir / settings['target']
    return Path(DEFAULT_TARGET).resolve()


def _discover_from_config(config_path: Path, target_dir: Path) -> List[SkillMapping]:
    """Discover skills from all sources in a config file."""
    config = load_config(config_path)
    config_dir = config_path.parent
    sources = config.get('sources', [])

    all_mappings: List[SkillMapping] = []
    for src in sources:
        src_type = src.get('type', 'auto')
        strategy_class = STRATEGIES.get(src_type)
        if strategy_class is None:
            raise ValueError(f"Unknown source type: {src_type}")

        if src_type == 'github':
            repo_url = src.get('path', '')
            tree = src.get('tree', 'master')
            subpath = src.get('subpath', 'skills')
            strategy = GitHubDiscovery(repo_url, target_dir, tree=tree, subpath=subpath)
        else:
            src_path = config_dir / src.get('path', '.')
            strategy = strategy_class(src_path, target_dir)

        all_mappings.extend(strategy.discover())

    return all_mappings


def _discover_single_source(args) -> List[SkillMapping]:
    """Discover skills from a single command-line source."""
    src_type = args.type
    src_path = args.path
    target_dir = Path(args.target).resolve() if args.target else Path(DEFAULT_TARGET).resolve()

    if not src_path:
        raise ValueError("--path is required when using --type")

    strategy_class = STRATEGIES.get(src_type)
    if strategy_class is None:
        raise ValueError(f"Unknown source type: {src_type}")

    if src_type == 'github':
        subpath = args.subpath if args.subpath else 'skills'
        strategy = GitHubDiscovery(src_path, target_dir, tree=args.tree, subpath=subpath)
    else:
        strategy = strategy_class(Path(src_path).resolve(), target_dir)

    return strategy.discover()


def _print_list(mappings: List[SkillMapping]) -> None:
    """Print SkillMapping list as a numbered list."""
    if not mappings:
        print("No skills discovered.")
        return

    for i, m in enumerate(mappings, start=1):
        skill_md = m.source_skill_md.name if m.source_skill_md else ''
        print(
            f"{i}. {m.skill_name} | "
            f"{'flat' if m.is_flat else 'directory'} | {skill_md}"
        )
        print(f"    Source: {m.source_path}")
        print(f"    Target: {m.target_path}")

    print(f"\nTotal: {len(mappings)} skill(s)")


def run(args):
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(message)s')

    try:
        if args.config:
            config_path = Path(args.config).resolve()
            if not config_path.exists():
                print(f"❌ Config not found: {config_path}", file=sys.stderr)
                sys.exit(1)
            target_dir = _resolve_target(
                config_path.parent,
                load_config(config_path).get('settings', {}),
                args.target,
            )
            mappings = _discover_from_config(config_path, target_dir)
        elif args.type:
            mappings = _discover_single_source(args)
        else:
            # Default: try to use ai-skills.yaml in current directory
            config_path = Path(DEFAULT_CONFIG).resolve()
            if config_path.exists():
                target_dir = _resolve_target(
                    config_path.parent,
                    load_config(config_path).get('settings', {}),
                    args.target,
                )
                mappings = _discover_from_config(config_path, target_dir)
            else:
                print(
                    "❌ No config file specified and no source type provided.\n"
                    "   Use --config <file> or --type <auto|directory|flat|github> --path <source>",
                    file=sys.stderr,
                )
                sys.exit(1)

        _print_list(mappings)

    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
