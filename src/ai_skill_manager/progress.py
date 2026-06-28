"""Progress callback helpers.

Provides a small callback type used by the service layer and a Rich-based
context manager that renders it as progress bars in the CLI.

Вспомогательные функции для отображения прогресса.
Предоставляют callback, используемый сервисным слоем, и контекстный менеджер
на базе Rich, который рендерит его в виде прогресс-баров в CLI.
"""

from contextlib import contextmanager
from typing import Callable, Dict, Generator

from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
)

ProgressCallback = Callable[[str, int, int], None]
"""Callable receiving ``(stage, current, total)``.

``stage`` is a stable identifier such as ``"discover"`` or ``"copy"``.
``current`` is the number of completed items so far.
``total`` is the expected total number of items.
"""

_STAGE_DESCRIPTIONS = {
    "discover": "Discovering skills",
    "validate": "Validating skills",
    "copy": "Copying skills",
    "adapt": "Adapting skills",
    "write_managed_state": "Writing managed state",
    "remove_orphans": "Removing orphans",
}


@contextmanager
def progress_context() -> Generator[ProgressCallback, None, None]:
    """Yield a progress callback backed by a Rich ``Progress`` display.

    Each distinct ``stage`` gets its own task. Tasks are created lazily on the
    first callback for that stage and removed automatically when the context
    exits (``transient=True``).
    """
    tasks: Dict[str, int] = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        transient=True,
    ) as progress:

        def callback(stage: str, current: int, total: int) -> None:
            task_id = tasks.get(stage)
            if task_id is None:
                task_id = progress.add_task(
                    _STAGE_DESCRIPTIONS.get(stage, stage),
                    total=total,
                )
                tasks[stage] = task_id
            else:
                progress.update(task_id, total=total)
            progress.update(task_id, completed=current)

        yield callback
