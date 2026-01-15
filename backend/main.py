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
# PART 2: Utility Routes
# ==========================================

@app.route('/api/schemas', methods=['GET'])
def get_schemas():
    """
    Returns available API schemas for frontend API block configuration.
    This is a utility endpoint that doesn't require authentication.
    """
    return jsonify(API_SCHEMAS)

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
