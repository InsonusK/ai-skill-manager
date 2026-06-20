"""Abstract base class for link builders."""

from abc import ABC
from typing import List, Tuple

from ...models import ContentContext, Link, LinkKind


class absLinkBuilder(ABC):
    def search(self, content: ContentContext) -> List[Link]:
        ...

    def _split_fragment(self, path: str) -> Tuple[str, str]:
        """Split a path into path and ``#fragment`` parts."""
        if "#" in path:
            path_clean, header = path.split("#", 1)
            return path_clean, f"#{header}"
        return path, ""

    def _is_image(self, raw: str) -> bool:
        return raw.startswith("!")

    def _get_kind(self, path: str) -> LinkKind:
        if self._is_relative(path):
            return LinkKind.relative
        elif self._is_os_absolute(path):
            return LinkKind.os_absolute
        elif self._is_repo_absolute(path):
            return LinkKind.repo_absolute
        else:
            raise ValueError(f"Cann't define kind of path:{path}")

    def _is_relative(self, path: str) -> bool:
        """Return True for links starting with ``./`` or ``../``."""
        return path.startswith(("./", "../"))

    def _is_os_absolute(self, path: str) -> bool:
        return path.startswith("/")

    def _is_repo_absolute(self, path: str) -> bool:
        """Return True for absolute repo-root paths containing ``/``."""
        return not path.startswith("/") and not self._is_relative(path)
