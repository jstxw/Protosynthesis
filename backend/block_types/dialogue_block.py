from blocks import Block
import time

class DialogueBlock(Block):
    """
    Displays a message during execution and optionally captures user input.
    """
    def __init__(self, name: str, message: str = "", x: float = 0.0, y: float = 0.0):
        super().__init__(name, block_type="DIALOGUE", x=x, y=y)
        self.user_response = None # A property to hold the response from the frontend
        
        self.register_input("trigger", data_type="any", hidden=True)
        self.register_input("message", data_type="string", default_value=message)
        
        # The output will hold the value entered by the user.
        self.register_output("response", data_type="string")

    def execute(self):
        self.user_response = None # Reset before waiting
        print(f"DialogueBlock '{self.name}' is waiting for user input...")
        
        # Block execution and wait for the frontend to provide a response
        # via the /api/execution/respond endpoint.
        while self.user_response is None:
            time.sleep(0.2) # Poll for the response
        
        self.outputs["response"] = self.user_response