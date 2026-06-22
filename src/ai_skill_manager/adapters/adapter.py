from ..entities import Skill

from .rules import Type, absAdapter, DEFAULT_RULES, List
from .models.adapter_message import AdapterMessage
from typing import Dict


class Adapter:

    def __init__(self, skills: List[Skill], adapter_list: List[Type[absAdapter]] = DEFAULT_RULES):
        adapter_names = [r.name() for r in adapter_list]
        assert len(adapter_names) == len(set(adapter_names)), (
            f"Rules must have unique names. Duplicates: "
            f"{[n for n in adapter_names if adapter_names.count(n) > 1]}"
        )
        self.__ac = absAdapter.Context(skills)
        self.__adapters = [adapter_cls(self.__ac)
                           for adapter_cls in adapter_list]

    def adapt(self, old_skill: Skill, new_skill: Skill) -> Dict[str, AdapterMessage]:
        results = {}
        for adapter in self.__adapters:
            msg = adapter.adapt(old_skill, new_skill)
            results[adapter.name()] = msg
        return results
