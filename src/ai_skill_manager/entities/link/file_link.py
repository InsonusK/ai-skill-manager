"""FileLink entity: one parsed link occurrence and its resolved target.

Сущность FileLink: одно распарсенное вхождение ссылки и её разрешённая цель.
"""

from __future__ import annotations

from dataclasses import dataclass

from .abs_link import absLink
from .link_target import LinkTarget


@dataclass(frozen=True)
class FileLink(absLink):
    """A single link found in a file, with its resolved target.

    Одна ссылка, найденная в файле, с её разрешённой целью.
    """

    target: LinkTarget
    """Resolved target this link points to. / Разрешённая цель, на которую указывает ссылка."""
