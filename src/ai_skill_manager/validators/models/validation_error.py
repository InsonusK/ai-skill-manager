"""Single validation error model.

Модель отдельной ошибки валидации.
"""

from .validation_severity import ValidationSeverity

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ValidationError:
    """Represents one validation error with a message, severity, and parameters.

    The ``message`` may contain placeholders such as ``{field}`` that are
    filled by ``params`` when formatted for display.

    Представляет одну ошибку валидации с сообщением, уровнем серьёзности
    и параметрами.

    ``message`` может содержать плейсхолдеры, например ``{field}``,
    которые заполняются из ``params`` при форматировании для вывода.
    """

    message: str
    """
    Human-readable message template.
    Example: "Missing required field: {field}"

    Шаблон сообщения для пользователя.
    Пример: "Missing required field: {field}"
    """

    severity: ValidationSeverity
    """Severity level of the error. / Уровень серьёзности ошибки."""

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
            f"severity={self.severity!r}, "
            f"params={self.params!r})"
        )

    def to_log(self) -> str:
        """Return a log-friendly representation with severity and message.

        Возвращает представление, удобное для логов, с уровнем серьёзности
        и сообщением.
        """
        return f"[{self.severity.upper()}] {self}"
