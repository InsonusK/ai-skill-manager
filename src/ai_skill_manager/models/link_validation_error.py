"""A link resolution failure, together with the skill and file it occurred in.

Ошибка резолюции ссылки вместе со скиллом и файлом, в которых она произошла.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LinkValidationError:
    """One link's resolution failure, with enough context to report it in place.

    Carried through ``SyncResult``/``SyncFailedError`` as-is (mixed in with
    plain ``str`` errors from other steps) so the CLI layer can group link
    failures by skill and file when rendering them, instead of each one
    repeating that context in its own message.

    Сбой резолюции одной ссылки с достаточным контекстом, чтобы сообщить о
    ней на месте. Передаётся через ``SyncResult``/``SyncFailedError`` как
    есть (вперемешку с обычными строковыми ошибками других шагов), чтобы
    слой CLI мог сгруппировать сбои ссылок по скиллу и файлу при выводе,
    вместо повторения этого контекста в каждом сообщении.
    """

    skill_name: str
    """Name of the skill the failing link was authored in.
    Имя скилла, в котором была написана ссылка с ошибкой."""

    skill_path: Path
    """That skill's path relative to its source repository's root (not an OS
    filesystem absolute path). / Путь этого скилла относительно корня
    репозитория его источника (не абсолютный путь файловой системы ОС)."""

    file_relative_path: Path
    """Path of the file, relative to the skill, that contains the link.
    Путь файла, содержащего ссылку, относительно скилла."""

    link_raw: str
    """The link exactly as written in the source file.
    Ссылка в точности как она написана в исходном файле."""

    message: str
    """Why resolution failed, without repeating the raw link text.
    Причина сбоя резолюции, без повторения сырого текста ссылки."""
