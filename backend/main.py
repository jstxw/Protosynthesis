from flask import Flask, jsonify, request
from flask_cors import CORS
from blocks import Block
from project import Project
from block_types.api_block import APIBlock
from block_types.logic_block import LogicBlock
from block_types.react_block import ReactBlock
from block_types.transform_block import TransformBlock
from block_types.string_builder_block import StringBuilderBlock
from api_schemas import API_SCHEMAS
import collections
import json

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# ==========================================
# PART 1: API Block Functionality & Execution Engine
# ==========================================

def execute_graph(start_blocks: list[Block], method: str = 'bfs'):
    """
    Executes the graph.
    """
    # 1. Discovery: Find all reachable blocks
    all_blocks = set()
    # We can use BFS or DFS here to discover nodes
    if method == 'dfs':
        stack = list(start_blocks)
        while stack:
            block = stack.pop()
            if block in all_blocks:
                continue
            all_blocks.add(block)
            for connectors in block.output_connectors.values():
                for connector in connectors:
                    stack.append(connector.target_block)
    else: # bfs
        queue = collections.deque(start_blocks)
        while queue:
            block = queue.popleft()
            if block in all_blocks:
                continue
            all_blocks.add(block)
            for connectors in block.output_connectors.values():
                for connector in connectors:
                    queue.append(connector.target_block)
    
    # 2. Build Dependency Graph & Calculate In-Degrees
    in_degree = {block: 0 for block in all_blocks}
    graph = {block: [] for block in all_blocks}
    
    for block in all_blocks:
        for connectors in block.output_connectors.values():
            for connector in connectors:
                target = connector.target_block
                if target in all_blocks:
                    graph[block].append(target)
                    in_degree[target] += 1

    # 3. Execution (Topological Sort)
    # Nodes with 0 in-degree are ready to execute
    ready_queue = collections.deque([b for b in all_blocks if in_degree[b] == 0])
    
    results = {}
    execution_order = []

    while ready_queue:
        current_block = ready_queue.popleft()
        execution_order.append(current_block.name)
        
        # Fetch inputs from upstream blocks
        current_block.fetch_inputs()
        
        # Execute the block
        print(f"Executing {current_block.name}...")
        current_block.execute()
        
        # Store results
        results[current_block.id] = {
            "name": current_block.name,
            "type": current_block.block_type,
            "outputs": current_block.outputs
        }

        # Propagate to neighbors
        for neighbor in graph[current_block]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                ready_queue.append(neighbor)
                
    return {
        "execution_order": execution_order,
        "block_results": results
    }

# ==========================================
# PART 2: Flask Linking to React Frontend
# ==========================================

# In-memory storage for the current project
current_project = Project("Demo Project")

@app.route('/api/execute', methods=['POST'])
def run_graph():
    """
    Endpoint to trigger graph execution.
    """
    global current_project
    if not current_project.blocks:
        return jsonify({"error": "No graph defined"}), 400

    method = request.args.get('method', 'bfs')
    
    # Identify start nodes (nodes with no input connectors active)
    # For simplicity, we can just pass all blocks and let the engine sort it out,
    # but passing known start nodes is more efficient.
    # Here we just pass all blocks in the project as potential start points for discovery.
    start_blocks = list(current_project.blocks.values())
    
    try:
        results = execute_graph(start_blocks, method=method)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/update_input', methods=['POST'])
def update_react_input():
    """
    Endpoint for React frontend to send user input values.
    """
    data = request.json
    block_id = data.get("block_id")
    value = data.get("value")
    
    block = current_project.blocks.get(block_id)
    if block and isinstance(block, ReactBlock):
        block.set_user_input(value)
        return jsonify({"status": "updated", "block_id": block_id})
    else:
        return jsonify({"error": "Block not found"}), 404

@app.route('/api/block/toggle_visibility', methods=['POST'])
def toggle_visibility():
    """
    Endpoint to toggle visibility of an input or output on a block.
    """
    data = request.json
    block_id = data.get("block_id")
    key = data.get("key")
    io_type = data.get("type") # "input" or "output"
    
    block = current_project.blocks.get(block_id)
    if not block:
        return jsonify({"error": "Block not found"}), 404
        
    if io_type == "input":
        block.toggle_input_visibility(key)
    elif io_type == "output":
        block.toggle_output_visibility(key)
    else:
        return jsonify({"error": "Invalid type"}), 400
        
    return jsonify({"status": "updated", "block_id": block_id})

@app.route('/api/block/add', methods=['POST'])
def add_block():
    """
    Endpoint to add a new block to the project.
    Expects JSON: { "type": "API", "name": "My Block", "x": 100, "y": 100, ...params }
    """
    data = request.json
    block_type = data.get("type")
    name = data.get("name", "New Block")
    x = data.get("x", 0)
    y = data.get("y", 0)
    
    new_block = None
    
    try:
        if block_type == "API":
            # Default to custom if not specified
            schema_key = data.get("schema_key", "custom")
            new_block = APIBlock(name, schema_key)
            # If custom, allow overriding url/method
            if schema_key == "custom":
                if "url" in data: new_block.url = data["url"]
                if "method" in data: new_block.method = data["method"]
                
        elif block_type == "LOGIC":
            operation = data.get("operation", "add")
            new_block = LogicBlock(name, operation)
        elif block_type == "REACT":
            new_block = ReactBlock(name)
        elif block_type == "TRANSFORM":
            t_type = data.get("transformation_type", "to_string")
            new_block = TransformBlock(name, t_type)
        elif block_type == "STRING_BUILDER":
            template = data.get("template", "")
            new_block = StringBuilderBlock(name, template)
        else:
            return jsonify({"error": f"Unknown block type: {block_type}"}), 400
            
        new_block.x = x
        new_block.y = y
        current_project.add_block(new_block)
        
        return jsonify({
            "status": "added", 
            "block": new_block.to_dict()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/block/remove', methods=['POST'])
def remove_block():
    """
    Endpoint to remove a block.
    Expects JSON: { "block_id": "..." }
    """
    data = request.json
    block_id = data.get("block_id")
    
    if block_id in current_project.blocks:
        current_project.remove_block(block_id)
        return jsonify({"status": "removed", "block_id": block_id})
    else:
        return jsonify({"error": "Block not found"}), 404

@app.route('/api/block/update', methods=['POST'])
def update_block():
    """
    Endpoint to update block properties (position, name, specific params).
    Expects JSON: { "block_id": "...", "x": 100, "y": 100, "name": "...", ... }
    """
    data = request.json
    block_id = data.get("block_id")
    
    block = current_project.blocks.get(block_id)
    if not block:
        return jsonify({"error": "Block not found"}), 404
        
    # Update common properties
    if "x" in data:
        block.x = data["x"]
    if "y" in data:
        block.y = data["y"]
    if "name" in data:
        block.name = data["name"]
        
    # Update specific properties based on type
    if isinstance(block, APIBlock):
        if "schema_key" in data:
            block.apply_schema(data["schema_key"])
        if "url" in data:
            block.url = data["url"]
        if "method" in data:
            block.method = data["method"]
    elif isinstance(block, LogicBlock):
        if "operation" in data:
            block.operation = data["operation"]
    elif isinstance(block, TransformBlock):
        if "transformation_type" in data:
            block.transformation_type = data["transformation_type"]
    elif isinstance(block, StringBuilderBlock):
        if "template" in data:
            block.template = data["template"]
            
    return jsonify({"status": "updated", "block": block.to_dict()})

@app.route('/api/connection/add', methods=['POST'])
def add_connection():
    """
    Endpoint to connect two blocks.
    Expects JSON: { "source_id": "...", "source_output": "...", "target_id": "...", "target_input": "..." }
    """
    data = request.json
    source_id = data.get("source_id")
    source_output = data.get("source_output")
    target_id = data.get("target_id")
    target_input = data.get("target_input")
    
    source = current_project.blocks.get(source_id)
    target = current_project.blocks.get(target_id)
    
    if not source or not target:
        return jsonify({"error": "Source or target block not found"}), 404
        
    try:
        # Check if connection already exists to avoid duplicates?
        # For now, just connect.
        source.connect(source_output, target, target_input)
        return jsonify({"status": "connected"})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/connection/remove', methods=['POST'])
def remove_connection():
    """
    Endpoint to remove a connection.
    Expects JSON: { "source_id": "...", "source_output": "...", "target_id": "...", "target_input": "..." }
    """
    data = request.json
    source_id = data.get("source_id")
    source_output = data.get("source_output")
    target_id = data.get("target_id")
    target_input = data.get("target_input")
    
    source = current_project.blocks.get(source_id)
    target = current_project.blocks.get(target_id)
    
    if not source or not target:
        return jsonify({"error": "Source or target block not found"}), 404
        
    # Find and remove the connector
    if source_output in source.output_connectors:
        connectors = source.output_connectors[source_output]
        to_remove = []
        for conn in connectors:
            if conn.target_block == target and conn.target_input_key == target_input:
                to_remove.append(conn)
        
        for conn in to_remove:
            connectors.remove(conn)
            # Also clear from target
            target.input_connectors[target_input] = None
            
        if to_remove:
            return jsonify({"status": "disconnected"})
    
    return jsonify({"error": "Connection not found"}), 404

@app.route('/api/graph', methods=['GET'])
def get_graph_structure():
    """
    Returns the current graph structure for the frontend to render.
    """
    nodes = []
    edges = []
    
    for block in current_project.blocks.values():
        # Prepare extra data for frontend rendering
        extra_data = {}
        if isinstance(block, APIBlock):
            extra_data["schema_key"] = block.schema_key
            extra_data["url"] = block.url
            extra_data["method"] = block.method
        
        nodes.append({
            "id": block.id,
            "name": block.name,
            "type": block.block_type,
            "x": block.x,
            "y": block.y,
            "inputs": list(block.inputs.keys()),
            "outputs": list(block.outputs.keys()),
            "hidden_inputs": list(block.hidden_inputs),
            "hidden_outputs": list(block.hidden_outputs),
            "menu_open": block.menu_open,
            "extra": extra_data
        })
        
        for output_key, connectors in block.output_connectors.items():
            for connector in connectors:
                edges.append({
                    "source": block.id,
                    "sourceHandle": output_key,
                    "target": connector.target_block.id,
                    "targetHandle": connector.target_input_key
                })

    return jsonify({"nodes": nodes, "edges": edges})

@app.route('/api/schemas', methods=['GET'])
def get_schemas():
    """Returns available API schemas."""
    return jsonify(API_SCHEMAS)

@app.route('/api/project/save', methods=['GET'])
def save_project():
    """Returns the project as a JSON string."""
    return current_project.to_json()

@app.route('/api/project/load', methods=['POST'])
def load_project():
    """Loads a project from a JSON string."""
    global current_project
    try:
        json_data = request.json
        # If the client sends the JSON object directly, dump it to string first
        # or adjust from_json to take a dict.
        # Assuming request.data is the raw string or request.json is the dict.
        if isinstance(json_data, dict):
            json_str = json.dumps(json_data)
        else:
            json_str = json_data
            
        current_project = Project.from_json(json_str)
        return jsonify({"status": "loaded", "project_name": current_project.name})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# --- Demo Setup ---
def setup_demo_project():
    """
    Sets up a sample project.
    """
    proj = Project("Demo Project")
    
    input_block = ReactBlock("User Name Input")
    input_block.set_user_input("World")
    input_block.x = 100
    input_block.y = 100
    
    logic_block = LogicBlock("Greeter", "add")
    logic_block.inputs["val_a"] = "Hello " 
    logic_block.x = 300
    logic_block.y = 100
    
    api_block = APIBlock("Echo API", "custom")
    api_block.url = "https://postman-echo.com/get"
    api_block.x = 500
    api_block.y = 100
    
    display_block = ReactBlock("Result Display")
    display_block.x = 700
    display_block.y = 100

    proj.add_block(input_block)
    proj.add_block(logic_block)
    proj.add_block(api_block)
    proj.add_block(display_block)

    input_block.connect("user_input", logic_block, "val_b")
    
    def to_params(data):
        return {"message": data}
    
    logic_block.connect("result", api_block, "params", modifier=to_params)
    api_block.connect("response_json", display_block, "display_data")
    
    return proj

if __name__ == '__main__':
    current_project = setup_demo_project()
    app.run(debug=True, port=5000)
