from blocks import Block
import json

class TransformBlock(Block):
    """
    Transforms data from one format to another.
    """
    def __init__(self, name: str, transformation_type: str = "to_string", fields: str = "", x: float = 0.0, y: float = 0.0):
        super().__init__(name, block_type="TRANSFORM", x=x, y=y)
        self._transformation_type = transformation_type
        self._fields = fields
        
        self._update_ports()

    @property
    def transformation_type(self):
        return self._transformation_type

    @transformation_type.setter
    def transformation_type(self, value):
        self._transformation_type = value
        self._update_ports()

    @property
    def fields(self):
        return self._fields

    @fields.setter
    def fields(self, value):
        self._fields = value
        self._update_ports()

    def _update_ports(self):
        # Clear existing ports
        for key in list(self.inputs.keys()):
            del self.inputs[key]
            if key in self.input_connectors: del self.input_connectors[key]
            if key in self.input_meta: del self.input_meta[key]
            
        for key in list(self.outputs.keys()):
            del self.outputs[key]
            if key in self.output_connectors: del self.output_connectors[key]
            if key in self.output_meta: del self.output_meta[key]

        if self.transformation_type in ["to_string", "to_json"]:
            self.register_input("input", data_type="any")
            self.register_output("result", data_type="any")
            
        elif self.transformation_type == "params_to_json":
            self.register_output("result", data_type="json")
            field_list = [f.strip() for f in self.fields.split(",") if f.strip()]
            for f in field_list:
                self.register_input(f, data_type="any")
        
        elif self.transformation_type == "get_key":
            self.register_input("json_obj", data_type="json")
            self.register_input("key", data_type="string")
            self.register_output("value", data_type="any")

    def execute(self):
        if self.transformation_type == "to_string":
            data = self.inputs.get("input")
            self.outputs["result"] = str(data)
        elif self.transformation_type == "to_json":
            data = self.inputs.get("input")
            try:
                self.outputs["result"] = json.loads(data)
            except:
                self.outputs["result"] = {}
        elif self.transformation_type == "params_to_json":
            result = {}
            field_list = [f.strip() for f in self.fields.split(",") if f.strip()]
            for f in field_list:
                result[f] = self.inputs.get(f)
            self.outputs["result"] = result
        elif self.transformation_type == "get_key":
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
        else:
            data = self.inputs.get("input")
            self.outputs["result"] = data

    def to_dict(self):
        data = super().to_dict()
        data["transformation_type"] = self.transformation_type
        data["fields"] = self.fields
        return data