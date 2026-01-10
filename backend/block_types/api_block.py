from blocks import Block
import requests
from api_schemas import API_SCHEMAS

class APIBlock(Block):
    """
    Block that makes an HTTP request.
    Can be configured with a specific schema.
    """
    def __init__(self, name: str, schema_key: str = "custom"):
        super().__init__(name, block_type="API")
        self.schema_key = schema_key
        self.apply_schema(schema_key)

    def apply_schema(self, schema_key: str):
        """Configures the block based on the selected schema."""
        if schema_key not in API_SCHEMAS:
            schema_key = "custom"
        
        schema = API_SCHEMAS[schema_key]
        self.schema_key = schema_key
        self.url = schema.get("url", "")
        self.method = schema.get("method", "GET")
        
        # Clear existing inputs/outputs if re-applying (careful with existing connections)
        # For simplicity in this hackathon, we assume this is called on init or full reset
        self.inputs = {}
        self.input_connectors = {}
        self.outputs = {}
        self.output_connectors = {}
        self.hidden_inputs = set()
        self.hidden_outputs = set()

        # Register Inputs
        for key, config in schema.get("inputs", {}).items():
            self.register_input(key, config.get("default"), hidden=False)
            
        # Register Outputs
        for key, config in schema.get("outputs", {}).items():
            self.register_output(key, hidden=False)

    def execute(self):
        # Collect inputs
        # If schema is 'custom', we expect params, headers, body
        # If schema is specific (e.g. agify), we expect 'name' which maps to a query param
        
        schema = API_SCHEMAS.get(self.schema_key, API_SCHEMAS["custom"])
        
        # Prepare request data
        req_url = self.url
        req_params = {}
        req_body = {}
        req_headers = {}

        if self.schema_key == "custom":
            # Custom block logic: inputs map directly to request parts
            if "url" in self.inputs:
                req_url = self.inputs["url"]
            req_params = self.inputs.get("params", {})
            req_headers = self.inputs.get("headers", {})
            req_body = self.inputs.get("body", {})
        else:
            # Schema-based logic: inputs map to query params or body based on method
            # This is a simplification. Real schemas would define where each input goes.
            # For now, we'll assume GET inputs -> params, POST inputs -> body
            for key in schema.get("inputs", {}):
                val = self.inputs.get(key)
                if val is not None:
                    if self.method == "GET":
                        req_params[key] = val
                    else:
                        req_body[key] = val

        try:
            if self.method.upper() == "GET":
                response = requests.get(req_url, params=req_params, headers=req_headers)
            elif self.method.upper() == "POST":
                response = requests.post(req_url, json=req_body, headers=req_headers, params=req_params)
            else:
                response = requests.request(self.method, req_url, params=req_params, headers=req_headers, json=req_body)
            
            # Map outputs
            if self.schema_key == "custom":
                self.outputs["status_code"] = response.status_code
                try:
                    self.outputs["response_json"] = response.json()
                except ValueError:
                    self.outputs["response_json"] = {"raw": response.text}
            else:
                # Map specific schema outputs
                try:
                    data = response.json()
                    for key in schema.get("outputs", {}):
                        # Simple mapping: output key matches JSON key
                        if key in data:
                            self.outputs[key] = data[key]
                        else:
                            self.outputs[key] = None # or data itself if root
                except:
                    pass # Handle error
                
        except Exception as e:
            # Fallback error handling
            if "error" in self.outputs:
                self.outputs["error"] = str(e)

    def to_dict(self):
        d = super().to_dict()
        d["schema_key"] = self.schema_key
        return d
