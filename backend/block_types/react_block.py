from blocks import Block

class ReactBlock(Block):
    """
    A special block that can both display data from the graph and provide
    user-entered data back into the graph.
    """
    def __init__(self, name: str, x: float = 0.0, y: float = 0.0):
        super().__init__(name, block_type="REACT", x=x, y=y)
        
        # Input to trigger execution if this block is part of a larger flow
        self.register_input("trigger", data_type="any", hidden=True)
        # Data to display IN the React component (when acting as a sink)
        self.register_input("display_data", data_type="any")
        
        # Data from a user TO the graph (when acting as a source)
        # If unconnected, this is a manual input on the frontend.
        self.register_input("user_input", data_type="string")
        self.register_output("value_out", data_type="string")

    def execute(self):
        # Pass the value from the 'user_input' port to the 'value_out' port.
        # This allows the block to act as a source for downstream blocks.
        self.outputs["value_out"] = self.inputs.get("user_input")
