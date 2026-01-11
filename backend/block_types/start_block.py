from blocks import Block

class StartBlock(Block):
    """
    A block that marks the starting point for graph execution.
    It has no inputs and one output to trigger the downstream flow.
    """
    def __init__(self, name: str = "Start", x: float = 0.0, y: float = 0.0):
        super().__init__(name, block_type="START", x=x, y=y)
        self.register_output("start_signal", data_type="boolean")

    def execute(self):
        """
        Sets the output to True to signal the start of execution.
        """
        self.outputs["start_signal"] = True