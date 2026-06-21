from .validation_severity import ValidationSeverity


from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ValidationError:
    message: str
    """
    example of message: "Missing required field: {field}"
    """
    severity: ValidationSeverity
    params: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """Для пользователя: форматированное."""
        return self.message.format(**self.params)

    def __repr__(self) -> str:
        """Для отладки: шаблон + параметры."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"severity={self.severity!r}, "
            f"params={self.params!r})"
        )

    def to_log(self) -> str:
        """Как в логах: severity + formatted message."""
        return f"[{self.severity.upper()}] {self}"