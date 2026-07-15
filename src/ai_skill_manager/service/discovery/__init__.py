"""Discovery service.

Groups everything related to finding skills for configured sources: the
``discover`` entry point and the pattern-matching strategies it uses
(``skill``).

Сервис обнаружения.
Группирует всё, что связано с поиском навыков по настроенным источникам:
точку входа ``discover`` и стратегии сопоставления паттернов, которые она
использует (``skill``).
"""

from .discover import discover

__all__ = [
    "discover",
]
