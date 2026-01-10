from backend.blocks import Block

class ReactBlock(Block):
    """
    Block that interfaces with the React frontend.
    Inputs to this block are sent to the frontend.
    Outputs from this block come from frontend inputs.
    """
    def __init__(self, name: str):
        super().__init__(name, block_type="REACT")
        
        # Data to send TO React (display variables)
        self.register_input("display_data")
        
        # Data received FROM React (user inputs)
        # In a real execution flow, these would be populated before execution starts
        self.register_output("user_input")

    def execute(self):
        # In a real backend execution, this block might just pass data through
        # or act as a terminal node for data collection.
        
        # For "display_data", we just hold it so the Flask app can read it later
        pass
    
    def set_user_input(self, value):
        """Helper to simulate receiving input from frontend before execution."""
        self.outputs["user_input"] = value
