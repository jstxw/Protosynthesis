from blocks import Block
import json

class GetKeyBlock(Block):
    """
    A block that extracts a value from a JSON object by its key.
    """
    def __init__(self, name: str, x: float = 0.0, y: float = 0.0):
        super().__init__(name, block_type="GET_KEY", x=x, y=y)
        self.register_input("json_obj", data_type="json")
        self.register_input("key", data_type="string") # This will be the manual input
        self.register_output("value", data_type="any")

    def execute(self):
        json_obj = self.inputs.get("json_obj")
        key = self.inputs.get("key")
        
        if not isinstance(json_obj, dict):
            try:
                json_obj = json.loads(json_obj) if isinstance(json_obj, str) else {}
            except:
                json_obj = {}
        
        if isinstance(json_obj, dict) and key is not None:
            self.outputs["value"] = json_obj.get(key)
        else:
            self.outputs["value"] = None