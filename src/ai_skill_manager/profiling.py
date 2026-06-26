"""Profiling helpers for the AI skill manager.

Provides a thin wrapper around :mod:`cProfile` so developers can quickly
measure where time is spent during synchronization or discovery.

Предоставляет тонкую обёртку над :mod:`cProfile` для быстрого измерения
времени выполнения операций синхронизации и обнаружения навыков.
"""

import cProfile
import functools
import io
import os
import pstats
import sys
from pathlib import Path
from typing import Callable, Optional

#: Environment variable that enables profiling for any command.
#: Переменная окружения, включающая профилирование для любой команды.
PROFILE_ENV_VAR = "AI_SKILL_MANAGER_PROFILE"

#: Default number of rows to print from the profile stats.
#: Количество строк статистики профилирования по умолчанию.
DEFAULT_TOP_ROWS = 20

#: Default output file for the raw profile dump.
#: Файл для сохранения сырых данных профилирования по умолчанию.
DEFAULT_DUMP_FILE = "ai-skill-manager.prof"


class Profiler:
    """Context manager that profiles a block of code.

    Контекстный менеджер, профилирующий блок кода.

    Example / Пример:
        >>> with Profiler() as profiler:
        ...     run_sync(sources, target_dir)
        >>> profiler.print_stats()
    """

    def __init__(
        self,
        dump_file: Optional[Path] = None,
        top_rows: int = DEFAULT_TOP_ROWS,
        sort_keys: Optional[tuple] = None,
    ):
        """Initialize the profiler.

        Args:
            dump_file: Optional path to save raw ``.prof`` data.
                Путь для сохранения сырых данных профилирования.
            top_rows: Number of rows to print for each stats table.
                Количество строк для каждой таблицы статистики.
            sort_keys: Keys used to sort printed stats.
                Ключи сортировки выводимой статистики.
        """
        self.dump_file = dump_file
        self.top_rows = top_rows
        self.sort_keys = sort_keys or ("cumulative", "time", "calls")
        self._profiler: Optional[cProfile.Profile] = None
        self._stats: Optional[pstats.Stats] = None

    def __enter__(self) -> "Profiler":
        """Start profiling.

        Returns:
            The profiler instance for chaining. / Экземпляр профайлера.
        """
        self._profiler = cProfile.Profile()
        self._profiler.enable()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop profiling and optionally dump raw stats."""
        if self._profiler is None:
            return
        self._profiler.disable()
        stream = io.StringIO()
        self._stats = pstats.Stats(self._profiler, stream=stream)
        self._stats.strip_dirs()
        if self.dump_file is not None:
            self._profiler.dump_stats(str(self.dump_file))

    @property
    def stats(self) -> Optional[pstats.Stats]:
        """Collected profile statistics.

        Returns:
            ``pstats.Stats`` instance or ``None`` if profiling has not finished.
        """
        return self._stats

    def print_stats(self, file=None) -> None:
        """Print sorted profile statistics.

        Args:
            file: Output stream (defaults to ``sys.stdout``).
                Поток для вывода статистики.
        """
        if self._stats is None:
            print("Profiling statistics are not available yet.", file=file)
            return

        out = file if file is not None else sys.stdout
        stream = self._stats.stream
        self._stats.stream = out  # type: ignore[assignment]

        print("\n=== PROFILING RESULTS ===\n", file=out)
        for sort_key in self.sort_keys:
            print(f"--- Sorted by {sort_key} ---", file=out)
            self._stats.sort_stats(sort_key)
            self._stats.print_stats(self.top_rows)
            print(file=out)

        self._stats.stream = stream


def profile_command(func: Callable) -> Callable:
    """Decorator that profiles a CLI command when ``--profile`` is enabled.

    The decorator reads the ``profile`` attribute from the argparse namespace.
    If it is ``True`` or if the ``AI_SKILL_MANAGER_PROFILE`` environment variable
    is set, the wrapped function is executed under :class:`Profiler`.

    Декоратор профилирует CLI-команду, если включён флаг ``--profile``
    или установлена переменная окружения ``AI_SKILL_MANAGER_PROFILE``.

    Args:
        func: CLI command function that receives an argparse namespace.
            Функция команды CLI, принимающая namespace argparse.

    Returns:
        Wrapped function. / Обёрнутая функция.
    """

    @functools.wraps(func)
    def wrapper(args) -> None:
        enabled = getattr(args, "profile", False) or os.environ.get(
            PROFILE_ENV_VAR, ""
        ).lower() in ("1", "true", "yes", "on")
        if not enabled:
            return func(args)

        dump_file: Optional[Path] = None
        dump_path = getattr(args, "profile_output", None)
        if dump_path:
            dump_file = Path(dump_path)

        with Profiler(dump_file=dump_file) as profiler:
            result = func(args)

        profiler.print_stats()
        if dump_file is not None:
            print(f"\nRaw profile saved to: {dump_file}")
        return result

    return wrapper


def is_profiling_enabled(args) -> bool:
    """Return whether profiling is enabled from args or environment.

    Args:
        args: Parsed argparse namespace. / Разобранный namespace argparse.

    Returns:
        ``True`` if profiling should be enabled.
    """
    return getattr(args, "profile", False) or os.environ.get(
        PROFILE_ENV_VAR, ""
    ).lower() in ("1", "true", "yes", "on")
