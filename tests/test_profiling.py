"""Tests for the profiling helpers.

Тесты для вспомогательных функций профилирования.
"""

import os
import tempfile
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

from ai_skill_manager.profiling import (
    DEFAULT_DUMP_FILE,
    PROFILE_ENV_VAR,
    Profiler,
    is_profiling_enabled,
    profile_command,
)


def _noop(_args):
    """Dummy CLI command that does nothing."""
    pass


def _work_command(_args):
    """Dummy CLI command that performs a small amount of work."""
    return sum(range(100))


def test_profiler_collects_stats():
    """Profiler should collect non-empty statistics."""
    with Profiler() as profiler:
        sum(range(1000))

    assert profiler.stats is not None


def test_profiler_print_stats_does_not_raise():
    """Printing stats should not raise when profiling has finished."""
    with Profiler() as profiler:
        sum(range(100))

    profiler.print_stats()


def test_profiler_dump_file_created():
    """Profiler should write a raw dump file when requested."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        dump_path = Path(tmp_dir) / "test.prof"
        with Profiler(dump_file=dump_path) as profiler:
            sum(range(100))

        assert dump_path.exists()
        assert dump_path.stat().st_size > 0
        assert profiler.stats is not None


def test_profile_command_disabled_by_default():
    """When profiling is disabled the wrapped function runs normally."""
    wrapped = profile_command(_work_command)
    args = Namespace(profile=False)

    result = wrapped(args)
    assert result == 4950


def test_profile_command_enabled_by_arg(capsys):
    """When --profile is set, stats are printed after the command."""
    wrapped = profile_command(_work_command)
    args = Namespace(profile=True, profile_output=None)

    result = wrapped(args)
    captured = capsys.readouterr()

    assert result == 4950
    assert "PROFILING RESULTS" in captured.out


def test_profile_command_enabled_by_env(capsys):
    """Profiling can be enabled via environment variable."""
    wrapped = profile_command(_work_command)
    args = Namespace(profile=False, profile_output=None)

    with patch.dict(os.environ, {PROFILE_ENV_VAR: "1"}):
        result = wrapped(args)

    captured = capsys.readouterr()
    assert result == 4950
    assert "PROFILING RESULTS" in captured.out


def test_profile_command_writes_dump_file(capsys):
    """When profile_output is set, a raw dump file is created."""
    wrapped = profile_command(_work_command)
    with tempfile.TemporaryDirectory() as tmp_dir:
        dump_path = Path(tmp_dir) / "cmd.prof"
        args = Namespace(profile=True, profile_output=str(dump_path))

        wrapped(args)
        captured = capsys.readouterr()

        assert dump_path.exists()
        assert "Raw profile saved to:" in captured.out


def test_is_profiling_enabled_from_args():
    """is_profiling_enabled returns True when args.profile is True."""
    args = Namespace(profile=True)
    assert is_profiling_enabled(args) is True


def test_is_profiling_enabled_from_env():
    """is_profiling_enabled returns True when the env var is set."""
    args = Namespace(profile=False)
    with patch.dict(os.environ, {PROFILE_ENV_VAR: "true"}):
        assert is_profiling_enabled(args) is True


def test_is_profiling_enabled_disabled():
    """is_profiling_enabled returns False when no profiling flag is set."""
    args = Namespace(profile=False)
    with patch.dict(os.environ, {}, clear=True):
        assert is_profiling_enabled(args) is False


def test_profiler_exit_without_enter_does_not_raise():
    """Exiting a Profiler that was never entered should be a no-op."""
    profiler = Profiler()
    profiler.__exit__(None, None, None)
    assert profiler.stats is None


def test_profiler_print_stats_before_run_warns(capsys):
    """Printing stats before profiling finishes prints a warning."""
    profiler = Profiler()
    profiler.print_stats()
    captured = capsys.readouterr()
    assert "not available yet" in captured.out
