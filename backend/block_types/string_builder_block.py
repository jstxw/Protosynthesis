import re
import json
from blocks import Block
from typing import Set

class StringBuilderBlock(Block):
    """
    A block that builds a string from a template and inputs.
    It dynamically creates input ports based on placeholders in the template string.
    e.g., "Hello <<name>>" will create an input port named "name".
    Uses <<variable>> as delimiter to avoid conflict with JSON {}.
    """
    def __init__(self, name: str, template: str = "", x: float = 0.0, y: float = 0.0):
        super().__init__(name, block_type="STRING_BUILDER", x=x, y=y)
        self._template = ""
        self.register_input("trigger", data_type="any", hidden=True)
        self.register_output("result", data_type="string")
        # Use the property setter to parse the initial template
        self.template = template

    @property
    def template(self) -> str:
        """Gets the template string."""
        return self._template

    @template.setter
    def template(self, new_template: str):
        """Sets the template string and updates inputs accordingly."""
        self._template = new_template
        self._update_inputs_from_template()

    def _update_inputs_from_template(self):
        """
        Parses the template to find placeholders and registers them as inputs.
        """
        # Find all placeholders like <<var_name>>
        placeholders: Set[str] = set(re.findall(r'<<(\w+)>>', self._template))

        current_inputs: Set[str] = set(self.inputs.keys())

        # Inputs to add
        new_inputs = placeholders - current_inputs
        for key in new_inputs:
            self.register_input(key, data_type="any")

    def execute(self):
        """
        Formats the template string with the values from the input ports.
        """
        def replace_match(match):
            key = match.group(1)
            val = self.inputs.get(key)
            if val is None:
                val = ""
            
            if isinstance(val, (dict, list)):
                try:
                    return json.dumps(val)
                except:
                    return str(val)
            return str(val)

        self.outputs["result"] = re.sub(r'<<(\w+)>>', replace_match, self.template)

    def to_dict(self):
        """Adds the template to the serialized block data."""
        data = super().to_dict()
        data["template"] = self.template
        return data
