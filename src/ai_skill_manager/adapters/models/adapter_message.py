"""Adapter message model.

Модель сообщения адаптера.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AdapterMessage:
    """Message returned by an adapter describing the changes it made.

    The ``message`` may contain placeholders such as ``{field}`` that are
    filled by ``params`` when formatted for display.

    Сообщение, возвращаемое адаптером, описывающее произведённые им
    изменения.

    ``message`` может содержать плейсхолдеры, например ``{field}``,
    которые заполняются из ``params`` при форматировании для вывода.
    """

    message: str
    """
    Human-readable message template.
    Example: "Adapted field: {field}"

    Шаблон сообщения для пользователя.
    Пример: "Adapted field: {field}"
    """

    params: dict[str, Any] = field(default_factory=dict)
    """Parameters used to format ``message``. / Параметры для форматирования ``message``."""

    def __str__(self) -> str:
        """Return the formatted message for end users.

        Возвращает отформатированное сообщение для конечных пользователей.
        """
        return self.message.format(**self.params)

    def __repr__(self) -> str:
        """Return a debug representation including template and parameters.

        Возвращает отладочное представление, включающее шаблон и параметры.
        """
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"params={self.params!r})"
        )

    def to_log(self) -> str:
        """Return the formatted message for logging.

        Возвращает отформатированное сообщение для логирования.
        """
        return str(self)
