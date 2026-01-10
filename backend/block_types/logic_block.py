from blocks import Block

class LogicBlock(Block):
    """
    Block for simple logic operations (e.g., merging strings, basic math).
    """
    def __init__(self, name: str, operation: str):
        super().__init__(name, block_type="LOGIC")
        self.operation = operation

        self.register_input("val_a")
        self.register_input("val_b")
        self.register_output("result")

    def execute(self):
        a = self.inputs.get("val_a")
        b = self.inputs.get("val_b")

        if self.operation == "add":
            # Can handle string concatenation or number addition
            if a is not None and b is not None:
                self.outputs["result"] = a + b
        elif self.operation == "equals":
            self.outputs["result"] = (a == b)
        else:
            self.outputs["result"] = None
