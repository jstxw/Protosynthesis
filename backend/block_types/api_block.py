import requests
import json
from blocks import Block
from api_schemas import API_SCHEMAS
from typing import Set

class APIBlock(Block):
    """
    A block that makes an HTTP request to an API, with dynamically
    configurable inputs and outputs based on a selected schema.
    """
    def __init__(self, name: str, schema_key: str = "custom", x: float = 0.0, y: float = 0.0):
        super().__init__(name, block_type="API", x=x, y=y)
        
        # Add a trigger input to ensure execution is always intentional
        self.register_input("trigger", data_type="any", hidden=True)

        # Core outputs that are always present
        self.register_output("response_json", data_type="json")
        self.register_output("status_code", data_type="number")
        self.register_output("error", data_type="string")
        self.core_outputs = set(self.outputs.keys())

        # Keep track of which inputs are core vs dynamic
        self.core_inputs = set(self.inputs.keys()) # Now includes 'trigger'

        self.schema_key = "custom"
        self.url = ""
        self.method = "GET"
        
        self.apply_schema(schema_key)

    def apply_schema(self, schema_key: str):
        """Applies a predefined schema, dynamically creating inputs and outputs."""
        self.schema_key = schema_key
        schema = API_SCHEMAS.get(schema_key, API_SCHEMAS["custom"])

        self.url = schema.get("url", "")
        self.method = schema.get("method", "GET")

        # Clear old dynamic ports
        self._clear_dynamic_inputs()
        self._clear_dynamic_outputs()

        schema_inputs = schema.get("inputs", {})
        if self.schema_key == "custom":
            # Special handling for the generic custom block
            for key, meta in schema_inputs.items():
                self.register_input(key, data_type=meta.get("type", "any"), default_value=meta.get("default"))
        else:
            # Handling for structured schemas
            for input_type in ["path", "params", "body", "headers"]:
                for key, meta in schema_inputs.get(input_type, {}).items():
                    self.register_input(key, data_type=meta.get("type", "any"), default_value=meta.get("default"))

        # Register new outputs from the schema
        for key, meta in schema.get("outputs", {}).items():
            self.register_output(key, data_type=meta.get("type", "any"))

    def execute(self):
        """Executes the API call, with validation and error handling."""
        # Reset all outputs
        for key in self.outputs:
            self.outputs[key] = None

        # Check trigger input. If connected and False/None, skip execution.
        # We check if 'trigger' is in inputs. If it's not connected, it might be None depending on fetch_inputs.
        # However, usually we want to run if NOT connected, or if connected and True.
        # But for explicit control flow, if it receives explicit False, it should stop.
        if self.inputs.get("trigger") is False:
            self.outputs['error'] = "Skipped: Trigger condition not met."
            return

        schema = API_SCHEMAS.get(self.schema_key, API_SCHEMAS["custom"])
        
        # --- Determine URL, Params, Body, Headers ---
        url = self.url
        params = {}
        body = {}
        headers = {}

        if self.schema_key == "custom":
            url = self.inputs.get("url", "")
            params = self.inputs.get("params", {})
            body = self.inputs.get("body", {})
            headers = self.inputs.get("headers", {})
        else:
            schema_inputs = schema.get("inputs", {})
            # Format URL with path parameters
            try:
                path_params = {key: self.inputs.get(key, "") for key in schema_inputs.get("path", {})}
                url = self.url.format(**path_params)
            except KeyError as e:
                self.outputs['error'] = f"Missing path parameter in URL: {e}"
                return
            
            # Gather query params and body data
            params = {key: self.inputs.get(key) for key in schema_inputs.get("params", {}) if self.inputs.get(key) is not None}
            body = {key: self.inputs.get(key) for key in schema_inputs.get("body", {}) if self.inputs.get(key) is not None}
            headers = {key: self.inputs.get(key) for key in schema_inputs.get("headers", {}) if self.inputs.get(key) is not None}

        # --- Validation ---
        if not url or not url.strip():
            self.outputs['error'] = "API URL is not set."
            return
        
        # --- Execute Request ---
        try:
            response = requests.request(
                method=self.method.upper(),
                url=url,
                params=params,
                json=body if self.method.upper() in ["POST", "PUT", "PATCH"] else None,
                headers=headers,
                timeout=10
            )
            self.outputs['status_code'] = response.status_code
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

            response_data = response.json()
            self.outputs['response_json'] = response_data

            # Map response data to dynamic outputs
            schema_outputs = schema.get("outputs", {})
            for key in schema_outputs:
                if key in response_data:
                    self.outputs[key] = response_data[key]

        except requests.exceptions.RequestException as e:
            error_msg = f"Network request failed: {e}"
            self.outputs['error'] = error_msg
            if e.response is not None:
                self.outputs['status_code'] = e.response.status_code
                try:
                    self.outputs['response_json'] = e.response.json()
                except json.JSONDecodeError:
                    self.outputs['response_json'] = {"error": "Response is not valid JSON", "content": e.response.text}

    def to_dict(self):
        """Adds API-specific properties to the serialized data."""
        data = super().to_dict()
        data['schema_key'] = self.schema_key
        data['url'] = self.url
        data['method'] = self.method
        return data

    def _clear_dynamic_inputs(self):
        """Removes all input ports except for the ones in core_inputs."""
        keys_to_remove = [k for k in self.inputs.keys() if k not in self.core_inputs]
        for key in keys_to_remove:
            if key in self.inputs: del self.inputs[key]
            if key in self.input_meta: del self.input_meta[key]
            if key in self.input_connectors: del self.input_connectors[key]

    def _clear_dynamic_outputs(self):
        """Removes all output ports except for the ones in core_outputs."""
        keys_to_remove = [k for k in self.outputs.keys() if k not in self.core_outputs]
        for key in keys_to_remove:
            if key in self.outputs: del self.outputs[key]
            if key in self.output_meta: del self.output_meta[key]
            if key in self.output_connectors: del self.output_connectors[key]