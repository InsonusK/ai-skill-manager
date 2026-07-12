"""Adapter data models.

Exports the message type returned by file adapters.

Модели данных адаптера.

Экспортирует тип сообщения, возвращаемый адаптерами файлов.
"""

from .adapter_message import AdapterMessage
from .sync_error import SyncError

__all__ = ["AdapterMessage", "SyncError"]
