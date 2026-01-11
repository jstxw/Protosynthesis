from blocks import Block

class LoopBlock(Block):
    """
    A block that iterates over a list.
    NOTE: The current execution engine is a single-pass DAG executor and does not
    support true control-flow loops. This block will only process the last item
    as a placeholder for future engine upgrades.
    """
    def __init__(self, name: str, x: float = 0.0, y: float = 0.0):
        super().__init__(name, block_type="LOOP", x=x, y=y)
        self.register_input("trigger", data_type="any", hidden=True)
        self.register_input("list", data_type="list")
        
        self.register_output("item", data_type="any")
        self.register_output("index", data_type="number")
        self.register_output("loop_body_signal", data_type="any")
        self.register_output("done_signal", data_type="any")

    def execute(self):
        print("!!! WARNING: The Loop Block is a placeholder. The current execution engine does not support control-flow loops. This block will only process the last item. !!!")
        my_list = self.inputs.get("list", [])
        if isinstance(my_list, list) and my_list:
            self.outputs["item"] = my_list[-1]
            self.outputs["index"] = len(my_list) - 1
        
        self.outputs["loop_body_signal"] = True
        self.outputs["done_signal"] = True