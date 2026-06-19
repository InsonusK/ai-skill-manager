"""GitHub skill source.

Источник навыков из GitHub.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from .source import Source


@dataclass(frozen=True)
class GitHubSource(Source):
    """Skills discovered from a GitHub repository.

    Навыки, обнаруженные в репозитории GitHub.
    """

    repo_url: str
    #: GitHub repository URL. / URL репозитория GitHub.

    tree: str = "master"
    #: Git tree, branch or tag to use. / Ветка, дерево или тег Git.

    subpath: Optional[Union[str, List[str]]] = None
    #: Subpath(s) inside the repository to scan. / Подпуть(и) внутри репозитория.

    @property
    def source_type(self) -> str:
        return "github"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.source_type,
            "repo_url": self.repo_url,
            "tree": self.tree,
            "subpath": self.subpath,
        }
