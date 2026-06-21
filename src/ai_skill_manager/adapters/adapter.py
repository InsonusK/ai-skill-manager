from ..entities import Skill

from .rules import absAdapter, DEFAULT_RULES,List


class Adapter:

    def __init__(self, rule_list: List[absAdapter] = DEFAULT_RULES):
        rule_names = [r.name for r in rule_list]
        assert len(rule_names) == len(set(rule_names)
                                      ), "Rules must have unique names"
        self.__rules = rule_list

    def adapt(self, skills: List[Skill]) -> None:
        return 