import json
from typing import List, Dict, Optional
from blocks import Block, Connector

# Import all block types to allow dynamic instantiation
from block_types.api_block import APIBlock
from block_types.logic_block import LogicBlock
from block_types.react_block import ReactBlock
from block_types.transform_block import TransformBlock
from block_types.string_builder_block import StringBuilderBlock

class Project:
    """
    Represents a project containing a collection of blocks and their connections.
    Supports serialization to and from JSON.
    """
    def __init__(self, name: str):
        self.name = name
        self.blocks: Dict[str, Block] = {} # id -> Block

    def add_block(self, block: Block):
        """Adds a block to the project."""
        self.blocks[block.id] = block

    def remove_block(self, block_id: str):
        """Removes a block and its connections."""
        if block_id in self.blocks:
            block = self.blocks[block_id]
            # Disconnect inputs
            for key, connector in block.input_connectors.items():
                if connector:
                    # Remove from source's output list
                    source = connector.source_block
                    if connector in source.output_connectors[connector.source_output_key]:
                        source.output_connectors[connector.source_output_key].remove(connector)
            
            # Disconnect outputs
            for key, connectors in block.output_connectors.items():
                for connector in connectors:
                    # Remove from target's input
                    target = connector.target_block
                    target.input_connectors[connector.target_input_key] = None
            
            del self.blocks[block_id]

    def to_json(self) -> str:
        """Exports the project to a JSON string."""
        data = {
            "name": self.name,
            "blocks": [],
            "connections": []
        }

        # Serialize Blocks
        for block in self.blocks.values():
            block_data = block.to_dict()
            # Add specific fields for subclasses if needed
            if isinstance(block, APIBlock):
                block_data["url"] = block.url
                block_data["method"] = block.method
                block_data["schema_key"] = block.schema_key
            elif isinstance(block, LogicBlock):
                block_data["operation"] = block.operation
            elif isinstance(block, TransformBlock):
                block_data["transformation_type"] = block.transformation_type
            elif isinstance(block, StringBuilderBlock):
                block_data["template"] = block.template
            
            data["blocks"].append(block_data)

        # Serialize Connections
        for block in self.blocks.values():
            for output_key, connectors in block.output_connectors.items():
                for connector in connectors:
                    data["connections"].append({
                        "source_id": connector.source_block.id,
                        "source_output": connector.source_output_key,
                        "target_id": connector.target_block.id,
                        "target_input": connector.target_input_key
                        # Note: Modifiers are hard to serialize if they are lambdas.
                        # For a robust system, modifiers should be named strategies or classes.
                    })
        
        return json.dumps(data, indent=4)

    @staticmethod
    def from_json(json_str: str) -> 'Project':
        """Creates a Project instance from a JSON string."""
        data = json.loads(json_str)
        project = Project(data["name"])
        
        # 1. Recreate Blocks
        id_map = {} # old_id -> new_block_instance (if we want to preserve IDs, we can)
        
        for block_data in data["blocks"]:
            b_type = block_data["block_type"]
            name = block_data["name"]
            
            block = None
            if b_type == "API":
                # Pass schema_key if present, otherwise default to custom
                schema_key = block_data.get("schema_key", "custom")
                block = APIBlock(name, schema_key)
                # If it was custom, we might need to restore url/method manually if they differ from schema default
                if schema_key == "custom":
                    block.url = block_data.get("url", "")
                    block.method = block_data.get("method", "GET")

            elif b_type == "LOGIC":
                block = LogicBlock(name, block_data.get("operation", "add"))
            elif b_type == "REACT":
                block = ReactBlock(name)
            elif b_type == "TRANSFORM":
                block = TransformBlock(name, block_data.get("transformation_type", "to_string"))
            elif b_type == "STRING_BUILDER":
                block = StringBuilderBlock(name, block_data.get("template", ""))
            
            if block:
                # Restore base properties
                block.id = block_data["id"] # Preserve ID for connection mapping
                block.x = block_data.get("x", 0.0)
                block.y = block_data.get("y", 0.0)
                block.menu_open = block_data.get("menu_open", False)
                
                # Restore visibility state
                if "hidden_inputs" in block_data:
                    block.hidden_inputs = set(block_data["hidden_inputs"])
                if "hidden_outputs" in block_data:
                    block.hidden_outputs = set(block_data["hidden_outputs"])
                
                # Restore inputs (static values)
                if "inputs" in block_data:
                    for k, v in block_data["inputs"].items():
                        if k in block.inputs:
                            block.inputs[k] = v
                
                project.add_block(block)
                id_map[block.id] = block

        # 2. Recreate Connections
        for conn_data in data["connections"]:
            source = id_map.get(conn_data["source_id"])
            target = id_map.get(conn_data["target_id"])
            
            if source and target:
                # We skip modifiers for now as they aren't serialized
                source.connect(
                    conn_data["source_output"],
                    target,
                    conn_data["target_input"]
                )
                
        return project
