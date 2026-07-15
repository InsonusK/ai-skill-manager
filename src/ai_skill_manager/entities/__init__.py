"""Public entity models for skills, files, links and sources.

Открытые модели сущностей для навыков, файлов, ссылок и источников.
"""

from .path_kind import PathKind

from .link import absLink, FileLink, LinkData, WebLink
from .source import GitHubSource, LocalSource, Source
