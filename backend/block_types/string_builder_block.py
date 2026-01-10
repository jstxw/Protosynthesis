from blocks import Block

class StringBuilderBlock(Block):
    """
    Block to concatenate strings or insert data into a template.
    Useful for building prompts.
    """
    def __init__(self, name: str, template: str = ""):
        super().__init__(name, block_type="STRING_BUILDER")
        self.template = template # e.g., "Hello {name}, your score is {score}"
        
        # We can dynamically register inputs based on the template, 
        # but for simplicity, we'll allow a fixed set of inputs or a dictionary input.
        # Here, we'll use a generic 'variables' input which expects a dictionary,
        # AND specific named inputs for common use cases.
        
        self.register_input("template", template) # Allow overriding template at runtime
        self.register_input("var_1")
        self.register_input("var_2")
        self.register_input("var_3")
        self.register_output("result")

    def execute(self):
        tmpl = self.inputs.get("template", "")
        
        # Collect available variables
        # In a more advanced version, we could parse the template to find required keys.
        # For now, we just support {var_1}, {var_2}, {var_3}
        
        format_args = {}
        if self.inputs.get("var_1") is not None:
            format_args["var_1"] = self.inputs["var_1"]
        if self.inputs.get("var_2") is not None:
            format_args["var_2"] = self.inputs["var_2"]
        if self.inputs.get("var_3") is not None:
            format_args["var_3"] = self.inputs["var_3"]
            
        try:
            # Use python's format string syntax
            # e.g. "User {var_1} said {var_2}"
            self.outputs["result"] = tmpl.format(**format_args)
        except KeyError as e:
            self.outputs["result"] = f"Error: Missing variable {str(e)}"
        except Exception as e:
            self.outputs["result"] = f"Error: {str(e)}"
