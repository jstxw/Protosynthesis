from blocks import Block

class LogicBlock(Block):
    """
    Performs simple logical or arithmetic operations.
    """
    def __init__(self, name: str, operation: str = "add", x: float = 0.0, y: float = 0.0):
        super().__init__(name, block_type="LOGIC", x=x, y=y)
        self.operation = operation
        
        self.register_input("val_a", data_type="any")
        self.register_input("val_b", data_type="any")
        self.register_output("result", data_type="any")
        self.register_output("if_true", data_type="boolean")
        self.register_output("if_false", data_type="boolean")

    def execute(self):
        val_a = self.inputs.get("val_a")
        val_b = self.inputs.get("val_b")
        
        try:
            # Arithmetic
            if self.operation == "add":
                try:
                    self.outputs["result"] = float(val_a) + float(val_b)
                except:
                    self.outputs["result"] = str(val_a) + str(val_b)
            elif self.operation == "subtract":
                self.outputs["result"] = float(val_a) - float(val_b)
            elif self.operation == "multiply":
                self.outputs["result"] = float(val_a) * float(val_b)
            elif self.operation == "divide":
                self.outputs["result"] = float(val_a) / float(val_b)
            
            # Comparison
            elif self.operation == "equals":
                self.outputs["result"] = (val_a == val_b)
            elif self.operation == "not_equals":
                self.outputs["result"] = (val_a != val_b)
            elif self.operation == "greater_than":
                self.outputs["result"] = (float(val_a) > float(val_b))
            elif self.operation == "less_than":
                self.outputs["result"] = (float(val_a) < float(val_b))
            
            # Logical
            elif self.operation == "and":
                self.outputs["result"] = bool(val_a) and bool(val_b)
            elif self.operation == "or":
                self.outputs["result"] = bool(val_a) or bool(val_b)
            else:
                self.outputs["result"] = None
        except:
            self.outputs["result"] = None

        # Set conditional triggers based on truthiness of the result
        is_true = bool(self.outputs["result"])
        self.outputs["if_true"] = True if is_true else False
        self.outputs["if_false"] = True if not is_true else False

    def to_dict(self):
        data = super().to_dict()
        data["operation"] = self.operation
        return data