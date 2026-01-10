import uuid
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Callable, Optional, Set

class Connector:
    """
    Represents a connection between two blocks.
    Can optionally modify the data passing through it.
    """
    def __init__(self, source_block: 'Block', source_output_key: str, target_block: 'Block', target_input_key: str, modifier: Optional[Callable[[Any], Any]] = None):
        self.source_block = source_block
        self.source_output_key = source_output_key
        self.target_block = target_block
        self.target_input_key = target_input_key
        self.modifier = modifier

    def transfer(self, data: Any) -> Any:
        if self.modifier:
            return self.modifier(data)
        return data

class Block(ABC):
    """
    Base class for all blocks.
    """
    def __init__(self, name: str, block_type: str, x: float = 0.0, y: float = 0.0):
        self.id = str(uuid.uuid4())
        self.name = name
        self.block_type = block_type
        self.x = x
        self.y = y
        
        # Stores the actual data values
        self.inputs: Dict[str, Any] = {} 
        self.outputs: Dict[str, Any] = {}
        
        # Stores the connections
        # input_key -> Connector (one source per input)
        self.input_connectors: Dict[str, Optional[Connector]] = {} 
        # output_key -> List[Connector] (multiple destinations per output)
        self.output_connectors: Dict[str, List[Connector]] = {} 
        
        # UI State: Visibility of inputs/outputs
        # If a key is in these sets, it is HIDDEN.
        self.hidden_inputs: Set[str] = set()
        self.hidden_outputs: Set[str] = set()
        
        # UI State: Does this block have a configuration menu open?
        # This is mostly for frontend state, but good to track if we persist state.
        self.menu_open: bool = False

    def register_input(self, key: str, default_value: Any = None, hidden: bool = False):
        """Defines an input slot for this block."""
        self.inputs[key] = default_value
        self.input_connectors[key] = None
        if hidden:
            self.hidden_inputs.add(key)

    def register_output(self, key: str, hidden: bool = False):
        """Defines an output slot for this block."""
        self.outputs[key] = None
        self.output_connectors[key] = []
        if hidden:
            self.hidden_outputs.add(key)

    def toggle_input_visibility(self, key: str):
        """Toggles visibility of an input."""
        if key in self.inputs:
            if key in self.hidden_inputs:
                self.hidden_inputs.remove(key)
            else:
                self.hidden_inputs.add(key)

    def toggle_output_visibility(self, key: str):
        """Toggles visibility of an output."""
        if key in self.outputs:
            if key in self.hidden_outputs:
                self.hidden_outputs.remove(key)
            else:
                self.hidden_outputs.add(key)

    def connect(self, output_key: str, target_block: 'Block', input_key: str, modifier: Optional[Callable[[Any], Any]] = None):
        """Connects an output of this block to an input of another block."""
        if output_key not in self.outputs:
            raise ValueError(f"Output '{output_key}' not found in block '{self.name}'")
        if input_key not in target_block.inputs:
            raise ValueError(f"Input '{input_key}' not found in target block '{target_block.name}'")
        
        connector = Connector(self, output_key, target_block, input_key, modifier)
        self.output_connectors[output_key].append(connector)
        target_block.input_connectors[input_key] = connector
        return connector

    def fetch_inputs(self):
        """
        Retrieves data from connected source blocks and populates self.inputs.
        This should be called before execute().
        """
        for key, connector in self.input_connectors.items():
            if connector:
                # Assume source block has already executed and outputs are ready
                source_data = connector.source_block.outputs.get(connector.source_output_key)
                self.inputs[key] = connector.transfer(source_data)

    @abstractmethod
    def execute(self):
        """
        Core logic of the block.
        Should read from self.inputs and write to self.outputs.
        """
        pass
    
    def to_dict(self):
        """
        Serialize block state to a dictionary.
        Subclasses should override this if they have extra properties to save.
        """
        return {
            "id": self.id,
            "name": self.name,
            "block_type": self.block_type,
            "x": self.x,
            "y": self.y,
            "inputs": self.inputs, 
            "hidden_inputs": list(self.hidden_inputs),
            "hidden_outputs": list(self.hidden_outputs),
            "menu_open": self.menu_open
        }

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name} ({self.id})>"
