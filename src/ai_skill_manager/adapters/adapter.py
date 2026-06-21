from ..entities import Skill

from .rules import absAdapter, DEFAULT_RULES,List


class Adapter:

    def __init__(self, adapter_list: List[absAdapter] = DEFAULT_RULES):
        adapter_names = [r.name() for r in adapter_list]
        assert len(adapter_names) == len(set(adapter_names)), (
            f"Rules must have unique names. Duplicates: "
            f"{[n for n in adapter_names if adapter_names.count(n) > 1]}"
        )
        self.__adapters = adapter_list

    def adapt(self, skills: List[Skill]) -> None:
        ac = absAdapter.Context(skills)
        for adapter_cls in self.__adapters:
            adapter:absAdapter = adapter_cls(ac)
            for skill in skills:
                adapter.adapt(skill)