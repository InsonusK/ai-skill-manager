from typing import List

from .abs_adapter import absAdapter
from .link_adapter import LinkAdapter
DEFAULT_RULES:List[absAdapter] = [LinkAdapter()]