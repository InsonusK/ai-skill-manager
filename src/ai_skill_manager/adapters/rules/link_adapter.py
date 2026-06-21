from .abs_adapter import absAdapter,Skill


class LinkAdapter(absAdapter):
    @property
    def version(self) -> int:
        """Adapter version for change detection."""
        return "1.0.0"

    
    def adapt(self, skill: Skill) -> None:
        """Modify file in place after copying."""
        