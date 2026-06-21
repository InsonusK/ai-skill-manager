from typing import List, Type

from .abs_adapter import absAdapter
from .link_adapter import LinkAdapter
DEFAULT_RULES:List[Type[absAdapter]] = [LinkAdapter]