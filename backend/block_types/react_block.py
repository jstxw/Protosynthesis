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

    def update_ports(self, inputs_list, outputs_list):
        """
        Synchronizes the block's inputs and outputs with the lists provided by the frontend.
        Preserves existing values/connections where possible.
        """
        # --- Sync Inputs ---
        new_input_keys = set(item['key'] for item in inputs_list)
        current_input_keys = set(self.inputs.keys())

        # Remove deleted inputs
        for key in current_input_keys - new_input_keys:
            del self.inputs[key]
            if key in self.input_meta: del self.input_meta[key]
            if key in self.input_connectors: del self.input_connectors[key]

        # Add/Update inputs
        for item in inputs_list:
            key = item['key']
            if key not in self.inputs:
                self.register_input(key, data_type=item.get('data_type', 'any'))

        # --- Sync Outputs ---
        new_output_keys = set(item['key'] for item in outputs_list)
        current_output_keys = set(self.outputs.keys())

        for key in current_output_keys - new_output_keys:
            del self.outputs[key]
            if key in self.output_meta: del self.output_meta[key]
            if key in self.output_connectors: del self.output_connectors[key]

        for item in outputs_list:
            key = item['key']
            if key not in self.outputs:
                self.register_output(key, data_type=item.get('data_type', 'any'))

    def to_dict(self):
        data = super().to_dict()
        data["jsx_code"] = self.jsx_code
        data["css_code"] = self.css_code
        return data
