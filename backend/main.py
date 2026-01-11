from flask import Flask, jsonify, request, Response, stream_with_context
from flask_cors import CORS
from blocks import Block
from project import Project
from block_types.api_block import APIBlock
from block_types.logic_block import LogicBlock
from block_types.react_block import ReactBlock
from block_types.transform_block import TransformBlock
from block_types.start_block import StartBlock
from block_types.string_builder_block import StringBuilderBlock
from block_types.wait_block import WaitBlock
from block_types.dialogue_block import DialogueBlock
from block_types.loop_block import LoopBlock
from api_schemas import API_SCHEMAS
from database import mongodb # Assuming this is used within Project class now
from api_routes import api_v2
from ai_routes import ai_bp
import collections
import json

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# Register the new authenticated API routes (v2)
app.register_blueprint(api_v2)

# Register AI assistant routes
app.register_blueprint(ai_bp)

# Register Gemini agent routes
from routes.agent_routes import agent_bp
app.register_blueprint(agent_bp)

# Initialize MongoDB connection
try:
    mongodb.connect()
    print("✓ MongoDB connection established")
except Exception as e:
    print(f"Warning: Failed to connect to MongoDB: {e}")
    print("Running in in-memory mode only.")

# ==========================================
# PART 1: API Block Functionality & Execution Engine
# ==========================================

def execute_graph(start_blocks: list[Block], all_blocks_map: dict[str, Block]):
    """
    Generator that discovers reachable nodes and executes them, yielding
    progress events as JSON strings.
    """
    # 1. Discovery: Find all blocks reachable from the start_blocks using BFS.
    reachable_blocks = set()
    queue = collections.deque(start_blocks)
    while queue:
        block = queue.popleft()
        if block in reachable_blocks:
            continue
        reachable_blocks.add(block)
        for connectors in block.output_connectors.values():
            for connector in connectors:
                queue.append(connector.target_block)

    # 2. Build Dependency Graph for the REACHABLE subgraph
    block_map = {b.id: b for b in reachable_blocks}
    in_degree = {b.id: 0 for b in reachable_blocks}
    # The graph stores dependencies: graph[u] = [v, w] means u -> v and u -> w
    graph = {b.id: [] for b in reachable_blocks}

    for block in reachable_blocks:
        for connectors in block.output_connectors.values():
            for connector in connectors:
                target = connector.target_block
                # Only create edges between nodes that are in our reachable set
                if target.id in block_map:
                    graph[block.id].append(target.id)
                    in_degree[target.id] += 1

    # 3. Execution (Topological Sort on the subgraph)
    ready_queue = collections.deque([b_id for b_id, degree in in_degree.items() if degree == 0])
    

    while ready_queue:
        current_block_id = ready_queue.popleft()
        current_block = block_map[current_block_id]
        
        # Fetch inputs from upstream blocks
        current_block.fetch_inputs()
        
        # Yield start event for immediate highlighting
        yield json.dumps({
            "type": "start",
            "block_id": current_block.id,
            "block_type": current_block.block_type,
            "inputs": current_block.inputs
        }) + "\n"
        
        # Execute the block
        try:
            print(f"Executing {current_block.name}...")
            current_block.execute()
            print(f"Result ({current_block.name}): {current_block.outputs}")
            
            # Yield success event
            yield json.dumps({
                "type": "progress",
                "block_id": current_block.id,
                "name": current_block.name,
                "block_type": current_block.block_type,
                "outputs": current_block.outputs,
                "inputs": current_block.inputs
            }) + "\n"
            
        except Exception as e:
            print(f"!!! Execution of block '{current_block.name}' failed: {e}")
            # Yield error event
            yield json.dumps({
                "type": "error",
                "block_id": current_block.id,
                "name": current_block.name,
                "error": str(e)
            }) + "\n"

        # Propagate to neighbors
        for neighbor_id in graph[current_block_id]:
            in_degree[neighbor_id] -= 1
            if in_degree[neighbor_id] == 0:
                ready_queue.append(neighbor_id)
    
    yield json.dumps({"type": "complete"}) + "\n"

# ==========================================
# PART 2: Flask Linking to React Frontend
# ==========================================

# ==============================================================================
# WARNING: The use of 'global current_project' is not thread-safe and will
# cause issues in a multi-user or multi-request environment. These routes
# should be refactored to be stateless, operating on a project_id passed
# in the URL, similar to the new routes in `api_routes.py`.
# ==============================================================================
# In-memory storage for the current project
current_project = Project("Demo Project")

@app.route('/api/execute', methods=['POST'])
def run_graph():
    """
    Endpoint to trigger graph execution.

    NOTE: This endpoint operates on the global project state and should be
    refactored to be stateless (e.g., POST /api/v2/projects/<project_id>/execute).
    """
    global current_project
    if not current_project.blocks:
        return jsonify({"error": "No graph defined"}), 400

    # Find all StartBlock instances to use as entry points for execution.
    start_nodes = [
        block for block in current_project.blocks.values()
        if isinstance(block, StartBlock)
    ]

    if not start_nodes:
        return jsonify({"error": "Execution failed: No 'Start' block found in the project. Add a Start block to define an entry point."}), 400

    # Return a streaming response
    return Response(
        stream_with_context(execute_graph(start_nodes, current_project.blocks)),
        mimetype='application/x-ndjson'
    )

@app.route('/api/block/toggle_visibility', methods=['POST'])
def toggle_visibility():
    """
    Endpoint to toggle visibility of an input or output on a block.

    NOTE: This endpoint operates on the global project state and should be
    refactored to be stateless.
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

    NOTE: This endpoint operates on the global project state and should be
    refactored to be stateless (e.g., POST /api/v2/projects/<project_id>/blocks).
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
            new_block = APIBlock(name, schema_key, x=x, y=y)
            # If custom, allow overriding url/method
            if schema_key == "custom":
                if "url" in data: new_block.url = data["url"]
                if "method" in data: new_block.method = data["method"]
                
        elif block_type == "LOGIC":
            operation = data.get("operation", "add")
            new_block = LogicBlock(name, operation, x=x, y=y)
        elif block_type == "REACT":
            jsx_code = data.get("jsx_code", "export default function MyComponent({ data_in, onWorkflowOutputChange }) {\n  return <div>Input: {JSON.stringify(data_in)}</div>;\n}")
            css_code = data.get("css_code", "/* CSS for your component */\ndiv {\n  padding: 10px;\n  border-radius: 5px;\n  background-color: #f0f0f0;\n}")
            new_block = ReactBlock(name, jsx_code=jsx_code, css_code=css_code, x=x, y=y)
        elif block_type == "TRANSFORM":
            t_type = data.get("transformation_type", "to_string")
            fields = data.get("fields", "")
            new_block = TransformBlock(name, t_type, fields=fields, x=x, y=y)
        elif block_type == "STRING_BUILDER":
            template = data.get("template", "")
            new_block = StringBuilderBlock(name, template, x=x, y=y)
        elif block_type == "START":
            new_block = StartBlock(name, x=x, y=y)
        elif block_type == "WAIT":
            delay = data.get("delay", 1.0)
            new_block = WaitBlock(name, delay=delay, x=x, y=y)
        elif block_type == "DIALOGUE":
            message = data.get("message", "")
            new_block = DialogueBlock(name, message=message, x=x, y=y)
        elif block_type == "LOOP":
            new_block = LoopBlock(name, x=x, y=y)
        else:
            return jsonify({"error": f"Unknown block type: {block_type}"}), 400
            
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

    NOTE: This endpoint operates on the global project state and should be
    refactored to be stateless.
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

    NOTE: This endpoint operates on the global project state and should be
    refactored to be stateless.
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
    elif isinstance(block, ReactBlock):
        if "jsx_code" in data:
            block.jsx_code = data["jsx_code"]
        if "css_code" in data:
            block.css_code = data["css_code"]
    elif isinstance(block, LogicBlock):
        if "operation" in data:
            block.operation = data["operation"]
    elif isinstance(block, TransformBlock):
        if "transformation_type" in data:
            block.transformation_type = data["transformation_type"]
        if "fields" in data:
            block.fields = data["fields"]
    elif isinstance(block, StringBuilderBlock):
        if "template" in data:
            block.template = data["template"]
    elif isinstance(block, WaitBlock):
        if "delay" in data:
            block.delay = float(data["delay"])
            
    return jsonify({"status": "updated", "block": block.to_dict()})

@app.route('/api/execution/respond', methods=['POST'])
def execution_respond():
    """
    Receives user input from a frontend dialogue prompt during execution
    and sets it on the corresponding block instance to unblock it.
    """
    data = request.json
    block_id = data.get("block_id")
    value = data.get("value")

    block = current_project.blocks.get(block_id)
    if block and isinstance(block, DialogueBlock):
        block.user_response = value
        return jsonify({"status": "received"})

    return jsonify({"error": "Block not found or not a dialogue block"}), 404

@app.route('/api/block/update_output_value', methods=['POST'])
def update_block_output_value():
    """
    Endpoint for the frontend to set the value of an output port.
    Used by interactive blocks like DialogueBlock.

    NOTE: This endpoint operates on the global project state and should be
    refactored to be stateless.
    """
    data = request.json
    block_id = data.get("block_id")
    output_key = data.get("output_key")
    value = data.get("value")

    block = current_project.blocks.get(block_id)
    if not block:
        return jsonify({"error": "Block not found"}), 404

    if output_key not in block.outputs:
        return jsonify({"error": f"Output '{output_key}' not found on block"}), 404

    block.outputs[output_key] = value

    return jsonify({"status": "updated", "block": block.to_dict()})

@app.route('/api/block/update_input_value', methods=['POST'])
def update_block_input_value():
    """
    Endpoint for the frontend to set the value of an unconnected input.

    NOTE: This endpoint operates on the global project state and should be
    refactored to be stateless.
    """
    data = request.json
    block_id = data.get("block_id")
    input_key = data.get("input_key")
    value = data.get("value")
    
    block = current_project.blocks.get(block_id)
    if not block:
        return jsonify({"error": "Block not found"}), 404
        
    if input_key not in block.inputs:
        return jsonify({"error": f"Input '{input_key}' not found on block"}), 404
    
    # In a real app, you might add type validation here based on block.input_meta
    block.inputs[input_key] = value
    
    return jsonify({"status": "updated", "block": block.to_dict()})

@app.route('/api/connection/add', methods=['POST'])
def add_connection():
    """
    Endpoint to connect two blocks.
    Expects JSON: { "source_id": "...", "source_output": "...", "target_id": "...", "target_input": "..." }

    NOTE: This endpoint operates on the global project state and should be
    refactored to be stateless.
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

    NOTE: This endpoint operates on the global project state and should be
    refactored to be stateless.
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

    NOTE: This endpoint operates on the global project state and should be
    refactored to be stateless (e.g., GET /api/v2/projects/<project_id>/graph).
    """
    nodes = []
    edges = []
    
    for block in current_project.blocks.values():
        # Use the block's own to_dict() method for serialization.
        # This is more robust and respects subclass-specific data.
        node_data = block.to_dict()

        # The frontend expects 'type', but to_dict() provides 'block_type'.
        # Let's align them for consistency.
        node_data['type'] = node_data.pop('block_type')

        nodes.append(node_data)
        
        for output_key, connectors in block.output_connectors.items():
            for connector in connectors:
                edge_id = f"edge-{block.id}-{output_key}-{connector.target_block.id}-{connector.target_input_key}"
                edges.append({
                    "id": edge_id,
                    "source": block.id,
                    "sourceHandle": output_key,
                    "target": connector.target_block.id,
                    "targetHandle": connector.target_input_key,
                    "type": "straight"
                })

    return jsonify({"nodes": nodes, "edges": edges})

@app.route('/api/schemas', methods=['GET'])
def get_schemas():
    """Returns available API schemas."""
    return jsonify(API_SCHEMAS)

@app.route('/api/project/save', methods=['GET'])
def save_project():
    """
    Returns the project as a JSON string.
    NOTE: This should be removed in favor of a stateless approach.
    """
    return current_project.to_json()

@app.route('/api/project/load', methods=['POST'])
def load_project():
    """
    Loads a project from a JSON string.
    NOTE: This should be removed in favor of a stateless approach.
    """
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

# ==============================================================================
# NOTE: The old MongoDB persistence endpoints have been removed.
# This functionality is now handled by the stateless, authenticated routes
# in `api_routes.py` (e.g., POST /api/v2/projects, GET /api/v2/projects).
# ==============================================================================

# --- Demo Setup ---
def setup_demo_project():
    """
    Sets up a sample project demonstrating a clear API flow.
    """
    proj = Project("API Demo Project")
    
    return proj

if __name__ == '__main__':
    current_project = setup_demo_project()
    app.run(debug=True, host='0.0.0.0', port=5001)
