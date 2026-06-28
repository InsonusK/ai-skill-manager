"""Web link model.

Модель веб-ссылки.
"""

from __future__ import annotations

from dataclasses import dataclass, InitVar
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .link_kind import LinkKind
from .abs_link import absLink
from .link_path import LinkPath

if TYPE_CHECKING:
    from ..skill_file import SkillFile


@dataclass(frozen=True)
class WebLink(absLink):
    """A link that points to a web or mailto/ftp URI.

    Ссылка, указывающая на веб- или mailto/ftp URI.

    Attributes:
        url: The web address (URL) of the link.
            Веб-адрес (URL) ссылки.
    """

    url: str
    skill_file_value: InitVar[Optional["SkillFile"]] = None
    header_value: InitVar[Optional[str]] = None
    is_image_value: InitVar[bool] = False

    def __post_init__(
        self,
        skill_file_value: Optional["SkillFile"],
        header_value: Optional[str],
        is_image_value: bool,
    ) -> None:
        """Store the common header and image flags and build path info.

        Сохранить общие флаги заголовка и изображения и собрать информацию о пути.
        """
        object.__setattr__(self, "header", header_value)
        object.__setattr__(self, "is_image", is_image_value)
        object.__setattr__(self, "skill_file", skill_file_value)
        #object.__setattr__(self, "kind", LinkKind.external)
        object.__setattr__(
            self,
            "path",
            LinkPath(
                kind=LinkKind.external,
                formatted=self.url,
                repo_path=self.url,
                os_path=Path(self.url),
                exists=False,
                has_explicit_md_suffix=False,
                is_inside_repo=False,
            ),
        )
