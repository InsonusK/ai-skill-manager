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
    def __subpath(self)->Optional[List[str]]:
        if self.subpath is None:
            return None
        if isinstance(self.subpath, list):
            return self.subpath
        return [self.subpath]
    
    def __str__(self)->str:
        subpath = self.__subpath or [] 
        path = "\n - ".join(subpath)
        return f"{self.repo_url} {self.tree}{path}"
    
    @property
    def source_type(self) -> str:
        """Return the source type identifier ``github``.

        Возвращает идентификатор типа источника ``github``.
        """
        return "github"

    def to_dict(self) -> Dict[str, Any]:
        """Return a serializable dictionary with source metadata.

        Возвращает сериализуемый словарь с метаданными источника.
        """
        return {
            "type": self.source_type,
            "repo_url": self.repo_url,
            "tree": self.tree,
            "subpath": self.__subpath,
        }
