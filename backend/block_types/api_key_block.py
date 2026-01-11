from blocks import Block
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

ENV_KEY_PREFIX = "READ_"

class ApiKeyBlock(Block):
    """
    A block to provide an API key from a .env file on the server.
    It scans for environment variables prefixed with `FLOW_API_KEY_`
    and allows the user to select one to output.
    """

    def __init__(self, name: str, selected_key: str = "", x: float = 0.0, y: float = 0.0):
        super().__init__(name, block_type="API_KEY", x=x, y=y)
        self.selected_key = selected_key
        self.available_keys = self._get_available_keys()

        # This trigger allows the block to be part of a control flow
        self.register_input("trigger", data_type="any", hidden=True)
        self.register_output("key", data_type="string")

    def _get_available_keys(self):
        """Scans environment variables for keys with the correct prefix."""
        keys = []
        for env_var in os.environ:
            if env_var.startswith(ENV_KEY_PREFIX):
                # Store the key name without the prefix
                keys.append(env_var[len(ENV_KEY_PREFIX):])
        return sorted(keys)

    def execute(self):
        """
        Outputs the selected API key's value from the environment variables.
        """
        if self.selected_key:
            full_env_var_name = f"{ENV_KEY_PREFIX}{self.selected_key}"
            print(full_env_var_name)

            self.outputs["key"] = os.getenv(full_env_var_name)
        else:
            self.outputs["key"] = None

    def to_dict(self):
        data = super().to_dict()
        data["selected_key"] = self.selected_key
        data["available_keys"] = self.available_keys
        return data