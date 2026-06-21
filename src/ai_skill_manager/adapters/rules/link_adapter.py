from .abs_adapter import absAdapter,Skill


class LinkAdapter(absAdapter):
    def __init__(self, adapter_context):
        super().__init__(adapter_context)
        
    @classmethod
    def version(cls) -> str:
        """Adapter version for change detection."""
        return "1.0.0"

    
    def adapt(self, skill: Skill) -> None:
        """Modify file in place after copying."""
        #TODO: сделать функционал который будет проходить по всем link в skill file и заменять их на skill format links