from blocks import Block

class ReactBlock(Block):
    """
    A block for creating interactive UI components with React.
    The code is edited and rendered on the frontend.
    """
    def __init__(self, name: str, jsx_code: str = "", css_code: str = "", x: float = 0.0, y: float = 0.0):
        super().__init__(name, block_type="REACT", x=x, y=y)
        self.jsx_code = jsx_code
        self.css_code = css_code
        
        # Default I/O for demonstration
        self.register_input("data_in", data_type="any")
        self.register_output("data_out", data_type="any")

    def execute(self):
        # The core logic is handled on the frontend.
        # The backend just acts as a data pass-through if needed.
        # For now, we do noting during server side execution.
        pass

    def to_dict(self):
        data = super().to_dict()
        data["jsx_code"] = self.jsx_code
        data["css_code"] = self.css_code
        return data
