import re
import json
from blocks import Block
from typing import Set

class StringBuilderBlock(Block):
    """
    A block that builds a string from a template and inputs.
    It dynamically creates input ports based on placeholders in the template string.
    e.g., "Hello {{name}}" will create an input port named "name".
    Uses {{variable}} syntax for template variables.
    """
    def __init__(self, name: str, template: str = "", x: float = 0.0, y: float = 0.0):
        super().__init__(name, block_type="STRING_BUILDER", x=x, y=y)
        self._template = ""
        self.register_input("trigger", data_type="any", hidden=True)
        # Add default message_text input for easy connection (explicitly NOT hidden)
        self.register_input("message_text", data_type="string", default_value="",
                          hidden=False,
                          placeholder="Connect from previous block",
                          description="Main text input for template")
        self.register_output("result", data_type="string")
        self.register_output("result_json", data_type="json")
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
        # Find all placeholders like {{var_name}}
        placeholders: Set[str] = set(re.findall(r'\{\{(\w+)\}\}', self._template))

        current_inputs: Set[str] = set(self.inputs.keys())
        # Don't count trigger and message_text as template-created inputs
        current_inputs.discard("trigger")
        current_inputs.discard("message_text")

        # Inputs to add (make them visible by default)
        new_inputs = placeholders - current_inputs
        for key in new_inputs:
            # Skip message_text since it's always present
            if key != "message_text":
                self.register_input(key, data_type="any", hidden=False)

    def execute(self):
        """
        Formats the template string with the values from the input ports.
        """
        print(f"\n🔧 STRING BUILDER DEBUG:")
        print(f"  Template: {repr(self.template)}")
        print(f"  Inputs: {self.inputs}")

        def replace_match(match):
            key = match.group(1)
            val = self.inputs.get(key)
            print(f"  Replacing {{{{{{key}}}}}} with: {repr(val)}")
            if val is None:
                val = ""

            if isinstance(val, (dict, list)):
                try:
                    return json.dumps(val)
                except:
                    return str(val)
            return str(val)

        result = re.sub(r'\{\{(\w+)\}\}', replace_match, self.template)
        print(f"  Final result: {repr(result)}\n")
        self.outputs["result"] = result

        # Try to parse as JSON and provide as result_json output
        try:
            self.outputs["result_json"] = json.loads(result)
            print(f"  ✅ Parsed as JSON successfully")
        except json.JSONDecodeError as e:
            print(f"  ⚠️  Not valid JSON, result_json will be None: {e}")
            self.outputs["result_json"] = None

    def to_dict(self):
        """Adds the template to the serialized block data."""
        data = super().to_dict()
        data["template"] = self.template
        return data
