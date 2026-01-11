import time
from blocks import Block

class WaitBlock(Block):
    """
    Pauses execution for a specified number of seconds.
    """
    def __init__(self, name: str, delay: float = 1.0, x: float = 0.0, y: float = 0.0):
        super().__init__(name, block_type="WAIT", x=x, y=y)
        self.delay = delay
        
        self.register_input("trigger", data_type="any", hidden=True)
        self.register_output("done", data_type="boolean")

    def execute(self):
        # This blocks the execution thread, creating a pause
        time.sleep(float(self.delay))
        self.outputs["done"] = True

    def to_dict(self):
        data = super().to_dict()
        data["delay"] = self.delay
        return data