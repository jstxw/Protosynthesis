from blocks import Block

class DialogueBlock(Block):
    """
    A block for displaying messages and capturing user response.
    """
    def __init__(self, name: str, message: str = "", x: float = 0.0, y: float = 0.0):
        super().__init__(name, block_type="DIALOGUE", x=x, y=y)
        
        self.register_input("trigger", data_type="any", hidden=True)
        self.register_input("message", data_type="string", default_value=message)
        self.register_input("require_input", data_type="boolean", default_value=False)
        self.register_input("mock_response", data_type="string", default_value="")
        
        self.register_output("response", data_type="string")

    def execute(self):
        msg = self.inputs.get("message", "")

        if self.inputs.get("require_input"):
            self.outputs["response"] = self.inputs.get("mock_response", "")
        else:
            self.outputs["response"] = msg