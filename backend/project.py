import json
from typing import List, Dict, Optional
from blocks import Block, Connector
from database import get_collection
from bson import ObjectId

# Import all block types to allow dynamic instantiation
from block_types.api_block import APIBlock
from block_types.logic_block import LogicBlock
from block_types.react_block import ReactBlock
from block_types.transform_block import TransformBlock
from block_types.start_block import StartBlock
from block_types.string_builder_block import StringBuilderBlock
from block_types.wait_block import WaitBlock
from block_types.dialogue_block import DialogueBlock
from block_types.api_key_block import ApiKeyBlock

class Project:
    """
    Represents a project containing a collection of blocks and their connections.
    Supports serialization to and from JSON and MongoDB persistence.
    """
    def __init__(self, name: str, project_id: Optional[str] = None):
        self.name = name
        self.blocks: Dict[str, Block] = {} # id -> Block
        self._id = project_id  # MongoDB ObjectId as string

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
            elif isinstance(block, ReactBlock):
                block_data["jsx_code"] = block.jsx_code
                block_data["css_code"] = block.css_code
            elif isinstance(block, LogicBlock):
                block_data["operation"] = block.operation
            elif isinstance(block, TransformBlock):
                block_data["transformation_type"] = block.transformation_type
                block_data["fields"] = block.fields
            elif isinstance(block, StringBuilderBlock):
                block_data["template"] = block.template
            elif isinstance(block, WaitBlock):
                block_data["delay"] = block.delay
            
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
            # Support both block_type (backend) and type (frontend/legacy) keys
            b_type = block_data.get("block_type") or block_data.get("type")
            if not b_type:
                continue # Skip invalid blocks

            name = block_data["name"]
            x = block_data.get("x", 0.0)
            y = block_data.get("y", 0.0)
            
            block = None
            if b_type == "API":
                # Pass schema_key if present, otherwise default to custom
                schema_key = block_data.get("schema_key", "custom")
                block = APIBlock(name, schema_key, x=x, y=y)
                # If it was custom, we might need to restore url/method manually if they differ from schema default
                if schema_key == "custom":
                    block.url = block_data.get("url", "")
                    block.method = block_data.get("method", "GET")

            elif b_type == "LOGIC":
                block = LogicBlock(name, block_data.get("operation", "add"), x=x, y=y)
            elif b_type == "REACT":
                block = ReactBlock(
                    name, 
                    jsx_code=block_data.get("jsx_code", ""), 
                    css_code=block_data.get("css_code", ""), 
                    x=x, y=y
                )
            elif b_type == "TRANSFORM":
                block = TransformBlock(name, block_data.get("transformation_type", "to_string"), fields=block_data.get("fields", ""), x=x, y=y)
            elif b_type == "STRING_BUILDER":
                block = StringBuilderBlock(name, block_data.get("template", ""), x=x, y=y)
            elif b_type == "START":
                block = StartBlock(name, x=x, y=y)
            elif b_type == "WAIT":
                block = WaitBlock(name, delay=block_data.get("delay", 1.0), x=x, y=y)
            elif b_type == "DIALOGUE":
                block = DialogueBlock(name, x=x, y=y)
            elif b_type == "API_KEY":
                block = ApiKeyBlock(name, x=x, y=y)
            
            if block:
                # Restore base properties
                block.id = block_data["id"] # Preserve ID for connection mapping
                block.menu_open = block_data.get("menu_open", False)
                
                # Restore visibility state
                if "hidden_inputs" in block_data:
                    block.hidden_inputs = set(block_data["hidden_inputs"])
                if "hidden_outputs" in block_data:
                    block.hidden_outputs = set(block_data["hidden_outputs"])
                
                # Restore inputs (static values)
                if "inputs" in block_data:
                    for input_data in block_data["inputs"]:
                        key = input_data.get("key")
                        value = input_data.get("value")
                        if key and key in block.inputs:
                            block.inputs[key] = value
                
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

    def save_to_db(self) -> str:
        """
        Saves the project to MongoDB.
        Returns the project ID (as string).
        """
        projects_collection = get_collection('projects')

        # Convert project to dict format
        project_data = json.loads(self.to_json())

        if self._id:
            # Update existing project
            projects_collection.update_one(
                {"_id": ObjectId(self._id)},
                {"$set": project_data}
            )
            return self._id
        else:
            # Insert new project
            result = projects_collection.insert_one(project_data)
            self._id = str(result.inserted_id)
            return self._id

    @staticmethod
    def load_from_db(project_id: str) -> 'Project':
        """
        Loads a project from MongoDB by ID.
        """
        projects_collection = get_collection('projects')

        project_data = projects_collection.find_one({"_id": ObjectId(project_id)})

        if not project_data:
            raise ValueError(f"Project with ID {project_id} not found")

        # Convert to JSON string for from_json method
        project_data_copy = project_data.copy()
        project_data_copy.pop('_id', None)  # Remove MongoDB _id field
        json_str = json.dumps(project_data_copy)

        # Create project using existing from_json method
        project = Project.from_json(json_str)
        project._id = str(project_data['_id'])

        return project

    @staticmethod
    def list_all_projects() -> List[Dict]:
        """
        Lists all projects in the database.
        Returns a list of project summaries.
        """
        projects_collection = get_collection('projects')

        projects = []
        for project_data in projects_collection.find():
            projects.append({
                "id": str(project_data['_id']),
                "name": project_data.get('name', 'Untitled'),
                "block_count": len(project_data.get('blocks', []))
            })

        return projects

    def delete_from_db(self) -> bool:
        """
        Deletes the project from MongoDB.
        Returns True if successful.
        """
        if not self._id:
            return False

        projects_collection = get_collection('projects')
        result = projects_collection.delete_one({"_id": ObjectId(self._id)})

        return result.deleted_count > 0

    def create_block(self, block_type: str, name: str, x: float, y: float, **kwargs) -> Optional[Block]:
        """Factory method to create and add a block to the project."""
        new_block = None
        if block_type == "API":
            schema_key = kwargs.get("schema_key", "custom")
            new_block = APIBlock(name, schema_key, x=x, y=y)
            if schema_key == "custom":
                if "url" in kwargs: new_block.url = kwargs["url"]
                if "method" in kwargs: new_block.method = kwargs["method"]
        elif block_type == "LOGIC":
            operation = kwargs.get("operation", "add")
            new_block = LogicBlock(name, operation, x=x, y=y)
        elif block_type == "REACT":
            jsx_code = kwargs.get("jsx_code", "export default function MyComponent({ data_in, onWorkflowOutputChange }) {\n  return <div>Input: {JSON.stringify(data_in)}</div>;\n}")
            css_code = kwargs.get("css_code", "/* CSS for your component */\ndiv {\n  padding: 10px;\n  border-radius: 5px;\n  background-color: #f0f0f0;\n}")
            new_block = ReactBlock(name, jsx_code=jsx_code, css_code=css_code, x=x, y=y)
        elif block_type == "TRANSFORM":
            t_type = kwargs.get("transformation_type", "to_string")
            fields = kwargs.get("fields", "")
            new_block = TransformBlock(name, t_type, fields=fields, x=x, y=y)
        elif block_type == "STRING_BUILDER":
            template = kwargs.get("template", "")
            new_block = StringBuilderBlock(name, template, x=x, y=y)
        elif block_type == "START":
            new_block = StartBlock(name, x=x, y=y)
        elif block_type == "WAIT":
            delay = kwargs.get("delay", 1.0)
            new_block = WaitBlock(name, delay=delay, x=x, y=y)
        elif block_type == "DIALOGUE":
            message = kwargs.get("message", "")
            new_block = DialogueBlock(name, message=message, x=x, y=y)
        elif block_type == "API_KEY":
            new_block = ApiKeyBlock(name, x=x, y=y)

        if new_block:
            self.add_block(new_block)

        return new_block

    def update_block(self, block_id: str, **kwargs) -> Optional[Block]:
        """Updates properties of a block in the project."""
        block = self.blocks.get(block_id)
        if not block:
            return None

        if "x" in kwargs:
            block.x = kwargs["x"]
        if "y" in kwargs:
            block.y = kwargs["y"]
        if "name" in kwargs:
            block.name = kwargs["name"]

        if isinstance(block, APIBlock):
            if "schema_key" in kwargs: block.apply_schema(kwargs["schema_key"])
            if "url" in kwargs: block.url = kwargs["url"]
            if "method" in kwargs: block.method = kwargs["method"]
        elif isinstance(block, ReactBlock):
            if "jsx_code" in kwargs: block.jsx_code = kwargs["jsx_code"]
            if "css_code" in kwargs: block.css_code = kwargs["css_code"]
        elif isinstance(block, LogicBlock):
            if "operation" in kwargs: block.operation = kwargs["operation"]
        elif isinstance(block, TransformBlock):
            if "transformation_type" in kwargs: block.transformation_type = kwargs["transformation_type"]
            if "fields" in kwargs: block.fields = kwargs["fields"]
        elif isinstance(block, StringBuilderBlock):
            if "template" in kwargs: block.template = kwargs["template"]
        elif isinstance(block, WaitBlock):
            if "delay" in kwargs: block.delay = float(kwargs["delay"])

        return block
