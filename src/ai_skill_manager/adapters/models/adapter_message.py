

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AdapterMessage:
    message: str
    """
    example of message: "Addapt field: {field}"
    """
    params: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """Для пользователя: форматированное."""
        return self.message.format(**self.params)

    def __repr__(self) -> str:
        """Для отладки: шаблон + параметры."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"params={self.params!r})"
        )

    def to_log(self) -> str:
        """Как в логах: severity + formatted message."""
        return str(self)