from blocks import Block
import json

class TransformBlock(Block):
    """
    Block for transforming data types (e.g., JSON to String, String to JSON, etc.).
    """
    def __init__(self, name: str, transformation_type: str):
        super().__init__(name, block_type="TRANSFORM")
        self.transformation_type = transformation_type
        
        self.register_input("input_data")
        self.register_output("output_data")

    def execute(self):
        data = self.inputs.get("input_data")
        
        try:
            if self.transformation_type == "to_string":
                self.outputs["output_data"] = str(data)
            elif self.transformation_type == "to_json":
                if isinstance(data, str):
                    self.outputs["output_data"] = json.loads(data)
                else:
                    self.outputs["output_data"] = data # Already an object?
            elif self.transformation_type == "json_dump":
                self.outputs["output_data"] = json.dumps(data)
            elif self.transformation_type == "to_int":
                self.outputs["output_data"] = int(data)
            elif self.transformation_type == "to_float":
                self.outputs["output_data"] = float(data)
            else:
                self.outputs["output_data"] = data
        except Exception as e:
            self.outputs["output_data"] = f"Error: {str(e)}"
