from flask import Flask, jsonify, request, Response, stream_with_context
from flask_cors import CORS
from blocks import Block
from project import Project
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
from block_types.api_block import APIBlock
from block_types.logic_block import LogicBlock
from block_types.react_block import ReactBlock, DEFAULT_JSX, DEFAULT_CSS
from block_types.transform_block import TransformBlock
from block_types.start_block import StartBlock
from block_types.string_builder_block import StringBuilderBlock
from block_types.wait_block import WaitBlock
from block_types.dialogue_block import DialogueBlock
from block_types.api_key_block import ApiKeyBlock
from api_schemas import API_SCHEMAS
from database import mongodb # Assuming this is used within Project class now
from api_routes import api_v2
from ai_routes import ai_bp
import collections
import json

app = Flask(__name__)

def get_cors_origins():
    """Get CORS origins from environment variable."""
    origins_str = os.getenv('CORS_ORIGINS', '')

    if not origins_str:
        print("WARNING: CORS_ORIGINS not set, defaulting to localhost only")
        return ['http://localhost:3000']

    origins = [origin.strip() for origin in origins_str.split(',')]
    print(f"CORS enabled for origins: {origins}")
    return origins

# Configure CORS with specific origins
CORS(app,
     resources={r"/api/*": {
         "origins": get_cors_origins(),
         "methods": ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         "allow_headers": ['Content-Type', 'Authorization', 'X-User-ID', 'x-user-id'],
         "supports_credentials": True,
         "expose_headers": ['Content-Type', 'Authorization']
     }})

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

def resolve_variables(obj, context):
    """
    Recursively resolve {{nodeId.field}} and {{field}} patterns in any data structure.

    Args:
        obj: The value to process (string, dict, list, or primitive)
        context: Dict with two sub-dicts:
                 - 'by_id': node ID -> outputs
                 - 'by_name': node name -> outputs
                 e.g., {"by_id": {"abc-123": {...}}, "by_name": {"OpenAI Chat API": {...}}}

    Returns:
        The same structure with variables resolved
    """
    import re

    if isinstance(obj, str):
        # Replace {{identifier.field}} patterns (supports both IDs and names)
        def replace_match(match):
            full_pattern = match.group(0)
            identifier = match.group(1)  # Could be node ID or name
            field = match.group(2) if match.lastindex >= 2 else None

            if field:  # {{identifier.field}} format
                # Try both by_id and by_name
                value = None
                if 'by_id' in context:
                    value = context['by_id'].get(identifier, {}).get(field)
                if value is None and 'by_name' in context:
                    value = context['by_name'].get(identifier, {}).get(field)
            else:
                return full_pattern

            if value is not None:
                # Convert to JSON string if it's a dict/list
                if isinstance(value, (dict, list)):
                    return json.dumps(value)
                return str(value)
            return full_pattern  # Keep original if not found

        # Pattern: {{identifier.field}} - supports spaces and hyphens for node names
        resolved = re.sub(r'\{\{([\w\s\-]+)\.([\w]+)\}\}', replace_match, obj)
        return resolved

    elif isinstance(obj, list):
        return [resolve_variables(item, context) for item in obj]

    elif isinstance(obj, dict):
        return {key: resolve_variables(value, context) for key, value in obj.items()}

    else:
        return obj  # Return primitives as-is


def execute_graph(start_blocks: list[Block], all_blocks_map: dict[str, Block]):
    """
    Generator that discovers reachable nodes and executes them, yielding
    progress events as JSON strings.
    """
    # Context to store all block outputs for variable substitution
    # Supports lookup by both node ID and node name
    execution_context = {
        'by_id': {},    # node_id -> outputs
        'by_name': {}   # node_name -> outputs
    }

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

        # Fetch inputs from upstream blocks FIRST
        current_block.fetch_inputs()

        # THEN resolve variables in block inputs using execution context
        print(f"\n🔍 Resolving variables for {current_block.name} (ID: {current_block.id})")
        print(f"  Context available by name: {list(execution_context.get('by_name', {}).keys())}")
        print(f"  Before resolution: {current_block.inputs}")

        current_block.inputs = resolve_variables(current_block.inputs, execution_context)

        # Also resolve variables in String Builder templates
        if hasattr(current_block, 'template'):
            print(f"  Template before resolution: {current_block.template}")
            current_block.template = resolve_variables(current_block.template, execution_context)
            print(f"  Template after resolution: {current_block.template}")

        print(f"  After resolution: {current_block.inputs}")

        # Yield start event for immediate highlighting
        yield json.dumps({
            "type": "start",
            "block_id": current_block.id,
            "block_type": current_block.block_type,
            "inputs": current_block.inputs
        }) + "\n"

        # Add 3 second delay before execution for visibility
        import time
        time.sleep(3)

        # Execute the block
        try:
            print(f"Executing {current_block.name}...")
            current_block.execute()
            print(f"Result ({current_block.name}): {current_block.outputs}")

            # Store outputs in context for variable substitution (by both ID and name)
            outputs_dict = dict(current_block.outputs)
            execution_context['by_id'][current_block.id] = outputs_dict
            execution_context['by_name'][current_block.name] = outputs_dict
            print(f"  ✅ Stored outputs in context:")
            print(f"     - By ID: {current_block.id}")
            print(f"     - By name: {current_block.name}")

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
# PART 2: Utility Routes
# ==========================================

@app.route('/api/schemas', methods=['GET'])
def get_schemas():
    """
    Returns available API schemas for frontend API block configuration.
    This is a utility endpoint that doesn't require authentication.
    """
    return jsonify(API_SCHEMAS)

@app.route('/api/execute', methods=['POST'])
def execute_workflow():
    """
    Execute a workflow from nodes and edges data.
    Accepts JSON payload with 'nodes' and 'edges' arrays.
    Returns streaming execution updates.
    """
    from flask import Response, stream_with_context
    from block_types.start_block import StartBlock
    from block_types.api_block import APIBlock
    from block_types.logic_block import LogicBlock
    from block_types.transform_block import TransformBlock
    from block_types.string_builder_block import StringBuilderBlock
    from block_types.wait_block import WaitBlock
    from block_types.dialogue_block import DialogueBlock
    from block_types.api_key_block import ApiKeyBlock
    from block_types.react_block import ReactBlock

    data = request.get_json()
    nodes_data = data.get('nodes', [])
    edges_data = data.get('edges', [])

    # Reconstruct blocks from node data
    blocks_map = {}
    start_blocks = []

    for node_data in nodes_data:
        node_id = node_data.get('id')
        block_type = node_data.get('data', {}).get('type') or node_data.get('data', {}).get('block_type')
        block_name = node_data.get('data', {}).get('name', 'Unnamed')

        # Create block based on type
        if block_type == 'START':
            block = StartBlock(name=block_name)
            start_blocks.append(block)
        elif block_type == 'API':
            schema_key = node_data.get('data', {}).get('schema_key', 'custom')
            block = APIBlock(name=block_name, schema_key=schema_key)
        elif block_type == 'LOGIC':
            operation = node_data.get('data', {}).get('operation', 'add')
            block = LogicBlock(name=block_name, operation=operation)
        elif block_type == 'TRANSFORM':
            transformation_type = node_data.get('data', {}).get('transformation_type', 'to_string')
            block = TransformBlock(name=block_name, transformation_type=transformation_type)
        elif block_type == 'STRING_BUILDER':
            template = node_data.get('data', {}).get('template', '')
            block = StringBuilderBlock(name=block_name, template=template)
        elif block_type == 'WAIT':
            delay = node_data.get('data', {}).get('delay', 1)
            block = WaitBlock(name=block_name, delay=delay)
        elif block_type == 'DIALOGUE':
            block = DialogueBlock(name=block_name)
        elif block_type == 'API_KEY':
            selected_key = node_data.get('data', {}).get('selected_key', '')
            block = ApiKeyBlock(name=block_name, selected_key=selected_key)
        elif block_type == 'REACT':
            block = ReactBlock(name=block_name)
        else:
            continue

        block.id = node_id

        # Set input values from node data
        inputs_data = node_data.get('data', {}).get('inputs', [])
        if isinstance(inputs_data, list):
            for inp in inputs_data:
                key = inp.get('key')
                value = inp.get('value')
                if key in block.inputs:
                    block.inputs[key] = value

        blocks_map[node_id] = block

    # Connect blocks based on edges
    for edge in edges_data:
        source_id = edge.get('source')
        target_id = edge.get('target')
        source_handle = edge.get('sourceHandle')
        target_handle = edge.get('targetHandle')

        if source_id in blocks_map and target_id in blocks_map:
            source_block = blocks_map[source_id]
            target_block = blocks_map[target_id]
            source_block.connect(source_handle, target_block, target_handle)

    def generate():
        try:
            for event in execute_graph(start_blocks, blocks_map):
                yield f"data: {event}\n\n"
        except Exception as e:
            error_event = json.dumps({
                "type": "error",
                "message": str(e)
            })
            yield f"data: {error_event}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

# ==============================================================================
# Production Multi-User Architecture
# ==============================================================================
# All workflow and project management is handled by authenticated v2 routes:
#   - POST   /api/v2/projects                           (create project)
#   - GET    /api/v2/projects                           (list all projects)
#   - GET    /api/v2/projects/<id>                     (get project)
#   - PUT    /api/v2/projects/<id>                     (update project)
#   - DELETE /api/v2/projects/<id>                     (delete project)
#   - POST   /api/v2/projects/<id>/workflows           (create workflow)
#   - GET    /api/v2/projects/<id>/workflows           (list workflows)
#   - GET    /api/v2/projects/<id>/workflows/<id>     (get workflow)
#   - PUT    /api/v2/projects/<id>/workflows/<id>     (update workflow)
#   - DELETE /api/v2/projects/<id>/workflows/<id>     (delete workflow)
#   - POST   /api/v2/projects/<id>/workflows/<id>/execute (execute workflow)
#
# See api_routes.py for implementation details.
# ==============================================================================

if __name__ == '__main__':
    # NOTE: setup_demo_project() is no longer called since we removed global state
    # The app now operates in a stateless manner using MongoDB for persistence
    # Demo projects can be created via the API: POST /api/v2/projects

    # Configuration from environment variables
    debug_mode = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')
    port = int(os.getenv('PORT', 5001))
    host = os.getenv('HOST', '127.0.0.1')  # Changed from 0.0.0.0 to localhost for security

    print(f"Starting Flask app on {host}:{port} (debug={debug_mode})")
    app.run(debug=debug_mode, host=host, port=port)
